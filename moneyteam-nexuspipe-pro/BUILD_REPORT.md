# BUILD REPORT — MONEYTEAM / NexusPipe Pro v4.4

Built and verified on 2026-09-24 in a clean Python 3.11 environment.
This report contains only checks that were actually executed — no claimed-but-unrun results.

## v4.4 — extensible signal-ingestion registry

| Module | Purpose |
|--------|---------|
| `app/services/signals.py` | Signal registry: `sim_market`, `document_text`, `blockchain_paper` (local, deterministic) + `web_probe`, `ocr_scan`, `rf_scan` (offline stubs that refuse to fabricate — status `offline_by_default`, 0 network calls) |
| `app/api/signal_routes.py` | `GET /api/v1/signals/sources` (honest availability), `POST /api/v1/signals/ingest` (admin, records append-only) |
| `app/services/lspa.py` | Intake phase now draws from the registry (`registry:sim_market`) instead of inline generation |
| `tests/test_signals.py` | 7 tests: availability honesty, unknown source, stub no-fabrication, determinism, document extraction, ingest persistence, stub-persists-nothing |

## Verification evidence (actual runs)

| Check | Command | Result |
|-------|---------|--------|
| Lint | `ruff check app scripts tests` | All checks passed |
| Test suite | `pytest -q` | **20 passed** (13 v4.3 + 7 v4.4) |
| Sources API | `GET /api/v1/signals/sources` | 3 local + 3 offline_stub, honest statuses |
| Ingest API | `POST /api/v1/signals/ingest` (document_text) | success, recorded in knowledge base |
| Offline stub | `POST /api/v1/signals/ingest` (web_probe) | `offline_by_default`, 0 network calls, nothing recorded |
| L.S.P.A. cycle | `POST /api/v1/lspa/cycle` | success, intake via registry, 0 network/live calls |
| Auth gate | ingest without token | 401 |

## Invariants (unchanged, enforced)

1. No verified provider receipt = no claimed execution.
2. No model load is ever claimed without telemetry evidence.
3. No fabricated data: offline stubs say they are offline.
4. Knowledge base is append-only; history is never rewritten.
5. Offline/paper defaults require explicit, audited human action to change.
