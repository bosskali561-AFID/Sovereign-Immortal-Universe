"""Core provider abstractions: receipts and safety exceptions."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class ProviderNotConfigured(RuntimeError):
    """Raised when a provider's package or credentials are missing."""


class LiveExecutionBlocked(RuntimeError):
    """Raised when a live operation is blocked by the safety gates."""


@dataclass
class ProviderReceipt:
    provider: str
    operation: str
    provider_id: str | None
    status: str
    raw: dict[str, Any] = field(default_factory=dict)
