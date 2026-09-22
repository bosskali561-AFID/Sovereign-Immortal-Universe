

def _session():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.db import Base
    import app.models  # noqa: F401  (register ORM mappings)

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_local_llm_disabled_reports_unavailable_honestly():
    from app.services.local_llm import local_llm_status

    status = local_llm_status()
    assert status["available"] is False
    assert status["source"] == "disabled"
    assert status["runtime"] == "unavailable"


def test_explanation_falls_back_to_template_when_disabled():
    from app.services.local_llm import explain_anomalies

    out = explain_anomalies(
        {
            "status": "success",
            "sample_count": 5,
            "q1": 10.0,
            "q3": 11.0,
            "iqr": 1.0,
            "lower_fence": 8.5,
            "upper_fence": 12.5,
            "anomaly_count": 1,
            "anomalies": [{"index": 4, "value": 99.5, "severity": "high"}],
        }
    )
    assert out["source"] == "template"
    assert "99.5" in out["text"] and "outlier" in out["text"]


def test_explanation_unreachable_falls_back_to_template():
    """LOCAL_LLM_ENABLED but the runtime is not there → honest fallback."""
    import importlib

    from app import config

    config.get_settings.cache_clear()
    import os

    os.environ["LOCAL_LLM_ENABLED"] = "true"
    os.environ["LOCAL_LLM_URL"] = "http://127.0.0.1:59999"  # nothing listens here
    try:
        importlib.reload(__import__("app.services.local_llm", fromlist=["explain_anomalies"]))
        from app.services.local_llm import explain_anomalies, local_llm_status

        status = local_llm_status()
        assert status["available"] is False
        assert status["source"] == "unreachable"
        out = explain_anomalies({"anomaly_count": 0, "sample_count": 5, "q1": 1, "q3": 2,
                                 "iqr": 1, "lower_fence": 0.5, "upper_fence": 2.5})
        assert out["source"] == "template"
    finally:
        os.environ.pop("LOCAL_LLM_ENABLED", None)
        os.environ.pop("LOCAL_LLM_URL", None)
        config.get_settings.cache_clear()
