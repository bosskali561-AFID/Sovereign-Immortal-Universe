from __future__ import annotations

from ..config import get_settings
from .provider_registry import provider_status


def production_readiness():
    s = get_settings()
    providers = provider_status()
    checks = {
        "environment_production": s.environment == "production",
        "database_configured": bool(s.database_url),
        "admin_auth_configured": bool(s.admin_token) if s.require_auth else True,
        "kill_switch_off": not s.kill_switch,
        "live_execution_flag": s.allow_live_execution,
        "financial_mode_live": s.financial_mode == "live",
        "trading_mode_live": s.trading_mode == "live",
        "stripe_configured": providers["providers"]["stripe"]["configured"],
        "coinbase_configured": providers["providers"]["coinbase"]["configured"],
    }
    return {
        "status": "READY" if all(checks.values()) else "NOT_READY",
        "checks": checks,
        "providers": providers,
        "execution_claims": "receipt_required",
    }
