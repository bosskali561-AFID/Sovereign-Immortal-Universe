def _session():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.db import Base
    import app.models  # noqa: F401  (register ORM mappings)

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_registry_lists_honest_availability():
    from app.services.signals import available_sources

    srcs = {s["name"]: s for s in available_sources()}
    assert srcs["sim_market"]["status"] == "available_local"
    assert srcs["document_text"]["status"] == "available_local"
    assert srcs["blockchain_paper"]["status"] == "available_local"
    assert srcs["web_probe"]["status"] == "offline_stub"
    assert srcs["ocr_scan"]["status"] == "offline_stub"
    assert srcs["rf_scan"]["status"] == "offline_stub"


def test_unknown_source_rejected():
    from app.services.signals import run_source

    out = run_source("does_not_exist")
    assert out["status"] == "error"
    assert "available_sources" in out


def test_offline_stub_never_fabricates():
    from app.services.signals import run_source

    out = run_source("web_probe")
    assert out["status"] == "offline_by_default"
    assert out["telemetry"]["network_calls"] == 0


def test_sim_market_is_deterministic():
    from app.services.signals import run_source

    a = run_source("sim_market", symbol="ETH-USDC", seed=7)
    b = run_source("sim_market", symbol="ETH-USDC", seed=7)
    assert a == b and a["status"] == "success"


def test_document_text_extracts_numbers():
    from app.services.signals import run_source

    out = run_source(
        "document_text",
        text="Invoice 12.5 and 13.1 and 99.2 and 10.0 and 10.5 total due",
    )
    assert out["status"] == "success"
    assert out["number_count"] == 5
    assert out["analysis"]["anomaly_count"] == 1  # 99.2 is the outlier


def test_ingest_records_to_knowledge_base():
    from app.services.knowledge import summary
    from app.services.signals import ingest

    db = _session()
    out = ingest(db, "sim_market", symbol="ETH-USDC", seed=42)
    assert out["status"] == "success"
    assert out["recorded"] is True
    assert summary(db)["signals_raw"] == 1


def test_ingest_offline_stub_records_nothing():
    from app.services.knowledge import summary
    from app.services.signals import ingest

    db = _session()
    out = ingest(db, "ocr_scan")
    assert out["status"] == "offline_by_default"
    assert summary(db)["signals_raw"] == 0
