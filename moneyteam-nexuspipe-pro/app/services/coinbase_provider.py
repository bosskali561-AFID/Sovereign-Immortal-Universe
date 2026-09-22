from __future__ import annotations

from typing import Any

from .providers import ProviderNotConfigured, ProviderReceipt
from .reliability import retry_provider

try:
    from coinbase.rest import RESTClient
except ImportError:  # pragma: no cover - optional dependency
    RESTClient = None


def _as_dict(value):
    return getattr(value, "to_dict", lambda: value)()


class CoinbaseAdvancedTradeProvider:
    name = "coinbase_advanced_trade"

    def __init__(self, api_key: str, api_secret: str, live: bool = False):
        if RESTClient is None:
            raise ProviderNotConfigured("coinbase-advanced-py is not installed")
        if not api_key or not api_secret:
            raise ProviderNotConfigured("COINBASE_API_KEY and COINBASE_API_SECRET are required")
        self.live = live
        self.client = RESTClient(api_key=api_key, api_secret=api_secret)

    @retry_provider
    def health(self) -> dict[str, Any]:
        perms = _as_dict(self.client.get_api_key_permissions())
        return {"provider": self.name, "live": self.live, "permissions": perms}

    @retry_provider
    def preview_order(self, **kwargs: Any) -> ProviderReceipt:
        raw = _as_dict(self.client.preview_order(**kwargs))
        return ProviderReceipt(self.name, "order.preview", raw.get("order_id"), "preview", raw)

    @retry_provider
    def create_order(self, **kwargs: Any) -> ProviderReceipt:
        raw = _as_dict(self.client.create_order(**kwargs))
        status = "success" if raw.get("success") else "failed"
        return ProviderReceipt(self.name, "order.create", raw.get("order_id"), status, raw)
