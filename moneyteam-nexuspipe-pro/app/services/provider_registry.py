from __future__ import annotations

from ..config import get_settings
from .coinbase_provider import CoinbaseAdvancedTradeProvider
from .providers import ProviderNotConfigured
from .stripe_provider import StripeProvider


def stripe_provider() -> StripeProvider:
    s = get_settings()
    if not s.stripe_secret_key:
        raise ProviderNotConfigured("STRIPE_SECRET_KEY is not configured")
    return StripeProvider(s.stripe_secret_key, live=s.stripe_live)


def coinbase_provider() -> CoinbaseAdvancedTradeProvider:
    s = get_settings()
    if not s.coinbase_api_key or not s.coinbase_api_secret:
        raise ProviderNotConfigured("COINBASE_API_KEY and COINBASE_API_SECRET are required")
    return CoinbaseAdvancedTradeProvider(s.coinbase_api_key, s.coinbase_api_secret, live=s.coinbase_live)


def provider_status() -> dict:
    s = get_settings()
    return {
        "providers": {
            "stripe": {"configured": bool(s.stripe_secret_key), "live": s.stripe_live},
            "coinbase": {
                "configured": bool(s.coinbase_api_key and s.coinbase_api_secret),
                "live": s.coinbase_live,
            },
            "openai": {"configured": bool(s.openai_api_key), "enabled": s.enable_openai},
        },
        "modes": {
            "trading_mode": s.trading_mode,
            "financial_mode": s.financial_mode,
            "allow_live_execution": s.allow_live_execution,
            "kill_switch": s.kill_switch,
            "require_human_approval": s.require_human_approval,
        },
    }
