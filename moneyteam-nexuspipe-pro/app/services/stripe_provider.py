from __future__ import annotations

from typing import Any

from .providers import ProviderNotConfigured, ProviderReceipt
from .reliability import retry_provider

try:
    import stripe
except ImportError:  # pragma: no cover - optional dependency
    stripe = None


class StripeProvider:
    name = "stripe"

    def __init__(self, api_key: str, live: bool = False):
        if stripe is None:
            raise ProviderNotConfigured("stripe package is not installed")
        if not api_key:
            raise ProviderNotConfigured("STRIPE_SECRET_KEY is not configured")
        if live and not api_key.startswith("sk_live_"):
            raise ProviderNotConfigured("STRIPE_LIVE requires an sk_live_ key")
        self.live = live
        self._stripe = stripe
        self._stripe.api_key = api_key

    @retry_provider
    def health(self) -> dict[str, Any]:
        account = self._stripe.Account.retrieve()
        return {
            "provider": self.name,
            "live": self.live,
            "account_id": account.get("id"),
            "charges_enabled": account.get("charges_enabled", False),
        }

    @retry_provider
    def create_payment_intent(
        self,
        *,
        amount: int,
        currency: str,
        idempotency_key: str,
        description: str | None = None,
    ) -> ProviderReceipt:
        params: dict[str, Any] = {
            "amount": amount,
            "currency": currency.lower(),
            "automatic_payment_methods": {"enabled": True},
        }
        if description:
            params["description"] = description
        intent = self._stripe.PaymentIntent.create(**params, idempotency_key=idempotency_key)
        raw = intent.to_dict_recursive() if hasattr(intent, "to_dict_recursive") else dict(intent)
        return ProviderReceipt(
            self.name, "payment_intent.create", raw.get("id"), raw.get("status", "unknown"), raw
        )
