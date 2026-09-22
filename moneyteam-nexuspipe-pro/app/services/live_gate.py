"""Single-use live execution gate: kill switch, approval token, provider live flag."""
from __future__ import annotations

from ..config import get_settings
from .providers import LiveExecutionBlocked


def require_live_ready(*, provider_live: bool, approval_token: str | None, admin_token: str = "") -> None:
    s = get_settings()
    if s.kill_switch:
        raise LiveExecutionBlocked("KILL_SWITCH is active; live execution is disabled")
    if not s.allow_live_execution:
        raise LiveExecutionBlocked("ALLOW_LIVE_EXECUTION is false")
    if s.require_human_approval:
        if not approval_token or not s.live_approval_token or approval_token != s.live_approval_token:
            raise LiveExecutionBlocked("Valid single-use live approval token required")
    if not provider_live:
        raise LiveExecutionBlocked("Provider is not configured for live mode")
