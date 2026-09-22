from pathlib import Path
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db import get_db
from ..models import Transaction, WebhookEvent
from ..security import require_admin
from ..services.audit import audit
from ..services.audio import normalize_audio_dir
from ..services.autonomous import run_cycle
from ..services.content import generate
from ..services.finance import process_transaction
from ..services.live_gate import require_live_ready
from ..services.ml_checker import evaluate_iqr
from ..services.payload import clean_payload
from ..services.provider_registry import coinbase_provider, provider_status, stripe_provider
from ..services.providers import LiveExecutionBlocked, ProviderNotConfigured
from ..services.readiness import production_readiness
from ..services.receipts import make_receipt, serialize_receipt

router = APIRouter(prefix="/api/v1")
settings = get_settings()


class FinanceRequest(BaseModel):
    tx_id: str = Field(min_length=3, max_length=128)
    rail: str
    amount: float = Field(gt=0)


class ContentRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=20000)


class ValuesRequest(BaseModel):
    values: list[float]


class StripeIntentRequest(BaseModel):
    amount: int = Field(gt=0)
    currency: str = Field(default="usd", min_length=3, max_length=3)
    idempotency_key: str = Field(min_length=3, max_length=255)
    description: str | None = Field(default=None, max_length=500)
    approval_token: str | None = None


class CoinbaseOrderRequest(BaseModel):
    product_id: str = Field(min_length=2, max_length=40)
    side: str
    order_configuration: dict
    approval_token: str | None = None


@router.get("/providers")
def providers():
    return provider_status()


@router.get("/readiness")
def readiness():
    return production_readiness()


@router.get("/health")
def health():
    return {
        "status": "ok",
        "version": settings.version,
        "environment": settings.environment,
        "trading_mode": settings.trading_mode,
        "financial_mode": settings.financial_mode,
    }


@router.post("/ml/check")
def ml_check(req: ValuesRequest):
    return evaluate_iqr(req.values)


@router.post("/payload/clean")
def payload_clean(payload: dict):
    return {"status": "success", "data": clean_payload(payload)}


@router.post("/financial/process")
def financial(req: FinanceRequest, db: Session = Depends(get_db)):
    try:
        return process_transaction(db, req.tx_id, req.rail, req.amount, settings.financial_mode)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except RuntimeError as e:
        raise HTTPException(503, str(e))


@router.post("/content/generate")
async def content(req: ContentRequest):
    result = await generate(req.prompt)
    if result["status"] == "blocked":
        raise HTTPException(403, detail=result)
    return result


@router.post("/engine/cycle")
async def cycle(db: Session = Depends(get_db), _: bool = Depends(require_admin)):
    try:
        return await run_cycle(db, settings.trading_mode, settings.financial_mode)
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.get("/receipts")
def receipts(limit: int = 50, db: Session = Depends(get_db), _: bool = Depends(require_admin)):
    limit = max(1, min(limit, 200))
    from ..models import Receipt

    rows = db.query(Receipt).order_by(Receipt.id.desc()).limit(limit).all()
    return [serialize_receipt(x) for x in rows]


@router.get("/transactions")
def transactions(limit: int = 50, db: Session = Depends(get_db), _: bool = Depends(require_admin)):
    limit = max(1, min(limit, 200))
    rows = db.query(Transaction).order_by(Transaction.id.desc()).limit(limit).all()
    return [
        {
            "tx_id": x.tx_id,
            "rail": x.rail,
            "amount": x.amount,
            "status": x.status,
            "created_at": x.created_at.isoformat(),
        }
        for x in rows
    ]


@router.post("/audio/normalize")
async def audio_normalize(file: UploadFile = File(...)):
    safe = Path(settings.storage_dir) / ("upload_" + uuid.uuid4().hex)
    safe.mkdir(parents=True, exist_ok=True)
    name = Path(file.filename or "audio.bin").name
    src = safe / name
    src.write_bytes(await file.read())
    out = safe / "normalized"
    try:
        results = normalize_audio_dir(safe, out)
        return {"status": "success", "files": [Path(x).name for x in results]}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/providers/stripe/payment-intent")
def stripe_payment_intent(req: StripeIntentRequest, db: Session = Depends(get_db), _: bool = Depends(require_admin)):
    try:
        provider = stripe_provider()
        require_live_ready(
            provider_live=provider.live,
            approval_token=req.approval_token,
            admin_token=settings.admin_token,
        )
        receipt = provider.create_payment_intent(
            amount=req.amount,
            currency=req.currency,
            idempotency_key=req.idempotency_key,
            description=req.description,
        )
        row = make_receipt(
            db,
            receipt.operation,
            receipt.status,
            True,
            {"provider": receipt.provider, "provider_id": receipt.provider_id, "raw": receipt.raw},
        )
        audit(db, "provider_execution", f"Stripe PaymentIntent {receipt.provider_id}")
        return {"status": "provider_executed", "receipt": serialize_receipt(row)}
    except ProviderNotConfigured as e:
        raise HTTPException(503, str(e))
    except LiveExecutionBlocked as e:
        raise HTTPException(403, str(e))
    except Exception as e:
        raise HTTPException(502, f"Stripe provider error: {e}")


@router.post("/providers/stripe/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        import stripe
    except ImportError:
        raise HTTPException(503, "stripe package is not installed")
    if not settings.stripe_webhook_secret:
        raise HTTPException(503, "STRIPE_WEBHOOK_SECRET is not configured")
    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")
    try:
        event = stripe.Webhook.construct_event(payload, signature, settings.stripe_webhook_secret)
    except Exception as e:
        raise HTTPException(400, f"Invalid Stripe webhook: {e}")
    event_id = event.get("id")
    existing = db.query(WebhookEvent).filter_by(event_id=event_id).first()
    if existing:
        return {"received": True, "event_id": event_id, "duplicate": True}
    row = WebhookEvent(
        provider="stripe",
        event_id=event_id,
        event_type=event.get("type", ""),
        processed=True,
        payload=event,
    )
    db.add(row)
    db.commit()
    audit(db, "webhook_received", f"Stripe {event_id}")
    return {"received": True, "event_id": event_id, "type": event.get("type")}


@router.get("/providers/coinbase/health")
def coinbase_health(_: bool = Depends(require_admin)):
    try:
        return coinbase_provider().health()
    except ProviderNotConfigured as e:
        raise HTTPException(503, str(e))
    except Exception as e:
        raise HTTPException(502, f"Coinbase provider error: {e}")


@router.post("/providers/coinbase/order")
def coinbase_order(req: CoinbaseOrderRequest, db: Session = Depends(get_db), _: bool = Depends(require_admin)):
    if req.side.upper() not in {"BUY", "SELL"}:
        raise HTTPException(400, "side must be BUY or SELL")
    try:
        provider = coinbase_provider()
        require_live_ready(
            provider_live=provider.live,
            approval_token=req.approval_token,
            admin_token=settings.admin_token,
        )
        receipt = provider.create_order(
            product_id=req.product_id,
            side=req.side.upper(),
            order_configuration=req.order_configuration,
        )
        verified = receipt.status == "success" and bool(receipt.provider_id)
        row = make_receipt(
            db,
            receipt.operation,
            receipt.status,
            verified,
            {
                "provider": receipt.provider,
                "provider_id": receipt.provider_id,
                "raw": receipt.raw,
            },
        )
        audit(db, "provider_execution", f"Coinbase order {receipt.provider_id}")
        return {
            "status": "provider_executed" if verified else "execution_not_verified",
            "receipt": serialize_receipt(row),
        }
    except ProviderNotConfigured as e:
        raise HTTPException(503, str(e))
    except LiveExecutionBlocked as e:
        raise HTTPException(403, str(e))
    except Exception as e:
        raise HTTPException(502, f"Coinbase provider error: {e}")
