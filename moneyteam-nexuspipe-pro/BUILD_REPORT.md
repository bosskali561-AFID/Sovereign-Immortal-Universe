# BUILD REPORT — MONEYTEAM / NexusPipe Pro v4.3

Built and verified on 2026-09-15 in a clean Python 3.11 environment.
This report contains only checks that were actually executed — no claimed-but-unrun results.

## v4.3 — missing modules implemented, integrated, executed

| Module | Purpose |
|--------|---------|
| `app/services/local_llm.py` | Ollama/local-LLM integration: the natural-language anomaly explanation engine. Offline-first (disabled by default), telemetry-verified, deterministic template fallback — source is always reported honestly |
| `app/api/ml_routes.py` | `POST /api/v1/ml/explain` — IQR analysis + natural-language explanation |
| `scripts/setup_local_llm.sh` | One-command local Ollama setup: install, `ollama pull`, runtime verification via `/api/tags` (refuses to claim success without telemetry) |
| `scripts/setup_android_workspace.sh` | Android Studio workspace setup: toolchain check, release keystore via keytool, gradle.properties guidance |
| `android/.../KeystoreHelper.java` | The AndroidKeyStore helper from the specification (KeyStore.getInstance → load(null) → getCertificate(alias) → getPublicKey()) |
| `migrations/versions/0002_knowledge_base.py` | Alembic migration for all knowledge-base tables (signals_raw, opportunities, winners, failures, audit_events) |
| `app/static/index.html` | Dashboard wired to health/readiness/config/knowledge/L.S.P.A./explain endpoints |
| `pyproject.toml` | Ruff + pytest configuration (lint gate now actually enforced) |

L.S.P.A. cycle now probes the local LLM honestly in the delegate phase
(`llm_source: disabled|unreachable|ollama`) and the report carries the anomaly
explanation with its true source.

## Verification evidence (actual runs)

| Check | Command | Result |
|-------|---------|--------|
| Lint | `ruff check app scripts tests` | All checks passed |
| Syntax compilation | `python -m compileall -q app scripts migrations tests` | PASS (exit 0) |
| Test suite | `pytest -q` | **13 passed** |
| Explanation endpoint | `POST /api/v1/ml/explain` | success, 1 anomaly, `source: template` (LLM disabled — honestly reported) |
| L.S.P.A. cycle | `POST /api/v1/lspa/cycle` (seed=7, top_n=3) | success, delegate `llm_source: disabled`, 0 network/live calls |
| Knowledge persistence | `GET /api/v1/knowledge/summary` | 3 signals, 3 opportunities, 3 winners recorded |
| Config redaction | `GET /api/v1/config` | all secrets `[REDACTED]`, `local_llm_enabled: false` exposed |
| Dashboard | `GET /` | 200, L.S.P.A. controls present |
| Unreachable-LLM fallback | unit test with `LOCAL_LLM_ENABLED=true` on a dead port | status `unreachable`, explanation falls back to `template` |

Setup scripts (`setup_local_llm.sh`, `setup_android_workspace.sh`) are written and
syntax-checked but intentionally NOT executed here — they install software and
create keystores on the operator's machine and require network access and a
`KEYSTORE_PASS`; run them where you deploy.

## Fixes carried forward

- v4.1: `app/security.py` import bug; `app/db.py` engine-singleton collision.
- v4.3: removed unused imports flagged by ruff; added `sample_count` to IQR output.

## Security posture (unchanged, enforced)

```
ALLOW_LIVE_EXECUTION=false   KILL_SWITCH=true
REQUIRE_HUMAN_APPROVAL=true   FINANCIAL_MODE=sandbox
TRADING_MODE=paper           REQUIRE_AUTH=true
LOCAL_LLM_ENABLED=false (offline-first)
```

Invariants: **no verified provider receipt = no claimed execution** and
**no model load is ever claimed without telemetry**.
