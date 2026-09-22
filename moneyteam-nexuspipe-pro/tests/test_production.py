import pytest


def test_readiness_defaults_not_live():
    from app.services.readiness import production_readiness

    r = production_readiness()
    assert r["status"] == "NOT_READY"
    assert r["checks"]["live_execution_flag"] is False


def test_coinbase_live_requires_credentials():
    from app.services.coinbase_provider import CoinbaseAdvancedTradeProvider

    with pytest.raises(Exception):
        CoinbaseAdvancedTradeProvider("", "", live=True)


def test_live_gate_blocks_by_default():
    from app.services.live_gate import require_live_ready
    from app.services.providers import LiveExecutionBlocked

    with pytest.raises(LiveExecutionBlocked):
        require_live_ready(provider_live=True, approval_token="anything", admin_token="x")


def test_stripe_live_requires_live_key():
    from app.services.providers import ProviderNotConfigured
    from app.services.stripe_provider import StripeProvider

    with pytest.raises(ProviderNotConfigured):
        StripeProvider("sk_test_123", live=True)


def test_payload_clean_redacts_secrets():
    from app.services.payload import clean_payload

    cleaned = clean_payload({"api_key": "abc", "nested": {"secret_token": "x", "name": "ok"}})
    assert cleaned["api_key"] == "[REDACTED]"
    assert cleaned["nested"]["secret_token"] == "[REDACTED]"
    assert cleaned["nested"]["name"] == "ok"


def test_ml_iqr_detects_outlier():
    from app.services.ml_checker import evaluate_iqr

    result = evaluate_iqr([10, 10.5, 11, 10.2, 99.5])
    assert result["status"] == "success"
    assert result["anomaly_count"] == 1


def test_security_module_imports():
    import app.security as security

    assert hasattr(security, "require_admin")
    assert hasattr(security, "require_https")
