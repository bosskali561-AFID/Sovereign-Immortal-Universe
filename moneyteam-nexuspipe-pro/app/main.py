from collections import defaultdict, deque
from pathlib import Path
from time import monotonic

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .api.knowledge_routes import router as knowledge_router
from .api.ml_routes import router as ml_router
from .api.routes import router as main_router
from .api.signal_routes import router as signal_router
from .config import get_settings
from .db import init_db

settings = get_settings()
Path(settings.storage_dir).mkdir(parents=True, exist_ok=True)
Path("data").mkdir(exist_ok=True)
init_db()

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Production control plane with provider-backed execution, receipts, approvals, "
    "knowledge base, six-phase L.S.P.A. cycle and the local-LLM explanation engine.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
if settings.environment == "production":
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts_list)

_hits: dict[str, deque] = defaultdict(deque)


@app.middleware("http")
async def security_and_rate_limit(request: Request, call_next):
    now = monotonic()
    key = request.client.host if request.client else "unknown"
    q = _hits[key]
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= settings.rate_limit_per_minute:
        return JSONResponse({"detail": "RATE_LIMITED"}, status_code=429)
    q.append(now)

    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    if settings.environment == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


app.include_router(main_router)
app.include_router(knowledge_router)
app.include_router(ml_router)
app.include_router(signal_router)


@app.get("/", include_in_schema=False)
def dashboard():
    return FileResponse("app/static/index.html")


@app.get("/ready")
def ready():
    from .services.readiness import production_readiness

    return production_readiness()
