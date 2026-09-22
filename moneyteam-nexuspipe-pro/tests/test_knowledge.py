def _session():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.db import Base
    import app.models  # noqa: F401  (register ORM mappings)

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_lspa_cycle_records_knowledge():
    from app.services.knowledge import summary
    from app.services.lspa import run_lspa_cycle

    db = _session()
    doc = run_lspa_cycle(db, seed=42, top_n=2)

    assert doc["status"] == "success"
    assert doc["runtime"] == "unavailable"  # honest telemetry: no artifact present
    assert doc["verification"]["passed"] is True
    assert doc["telemetry"]["network_calls"] == 0
    assert doc["telemetry"]["live_trades"] == 0
    assert doc["telemetry"]["anomaly_explanation"]["source"] == "template"

    s = summary(db)
    assert s["signals_raw"] == 3
    assert s["opportunities"] == 3
    assert s["winners"] + s["failures"] == 2


def test_knowledge_is_append_only():
    from app.services.knowledge import record_signal, summary

    db = _session()
    record_signal(db, "test", {"a": 1})
    record_signal(db, "test", {"a": 2})
    assert summary(db)["signals_raw"] == 2


def test_config_redacts_secrets():
    from app.config import get_settings
    from app.services.payload import clean_payload

    safe = clean_payload(get_settings().model_dump())
    assert safe.get("admin_token") == "[REDACTED]"
    assert safe.get("live_approval_token") == "[REDACTED]"
    assert safe.get("stripe_secret_key") == "[REDACTED]"
    assert safe.get("trading_mode") == "paper"
