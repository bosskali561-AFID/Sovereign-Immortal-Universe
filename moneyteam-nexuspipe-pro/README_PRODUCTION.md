# MONEYTEAM / NexusPipe Pro v4.1 — Production

This package contains provider-backed production infrastructure for Stripe and
Coinbase Advanced Trade. It contains **no real credentials** and does **not**
activate real-money execution by default.

## v4.1 changes

- Patched `app/security.py`: `from ..config import get_settings` →
  `from .config import get_settings` (the v4.0 package was broken on import).
- Added the supporting service modules that `app/` references
  (`db.py`, `services/providers.py`, `services/receipts.py`, `services/live_gate.py`,
  `services/provider_registry.py`, `services/payload.py`, `services/finance.py`,
  `services/content.py`, `services/ml_checker.py`, `services/autonomous.py`,
  `services/audio.py`, `app/static/index.html`) so the package is self-contained
  and importable.

## Production gates

- authenticated admin control
- least-privilege provider credentials
- HTTPS enforcement (production)
- rate limiting
- provider retries/backoff
- Stripe webhook signature verification + deduplication
- PostgreSQL/Alembic support
- backup script
- health/readiness endpoints
- audit events
- execution receipts with evidence hashes
- human approval (single-use live approval token)
- global kill switch
- CI (compile, tests, lint)

## Important

`ALLOW_LIVE_EXECUTION=false` and `KILL_SWITCH=true` are deliberate secure defaults.
Actual provider authorization and final live activation require the account owner
to configure production credentials/scopes and complete
`PRODUCTION_LIVE_RUNBOOK.md`. No verified provider receipt = no claimed execution.

## Run locally (paper mode)

```bash
cp .env.example .env
pip install -r requirements.txt
python -m compileall -q app scripts
pytest -q
uvicorn app.main:app --port 8000
```

## Deploy

```bash
cp .env.production.example .env.production  # fill in real values
docker compose -f docker-compose.production.yml up --build
```

## v4.2 — data / knowledge / configuration integration

- `app/services/knowledge.py` — additive knowledge base: every signal, opportunity,
  winner and failure is recorded append-only and never deleted.
- `app/services/lspa.py` — the six-phase L.S.P.A. cycle (Intake → Plan → Delegate →
  Execute → Verify → Report) as a first-class service. Paper mode only, offline,
  honest runtime telemetry (reports `unavailable` when no GGUF/MNN artifact exists).
- `app/api/knowledge_routes.py` — `POST /api/v1/lspa/cycle`, `GET /api/v1/config`
  (secrets redacted), `GET /api/v1/knowledge/{summary,opportunities,leaderboard}`.
- `scripts/run_lspa_cycle.py [seed] [top_n]` — run one cycle offline from the CLI.

## v4.3 — local LLM, Android workspace, complete migrations

- `app/services/local_llm.py` — Ollama integration for natural-language anomaly
  explanations. Offline-first: `LOCAL_LLM_ENABLED=false` by default; the engine
  probes the runtime with real telemetry and falls back to a deterministic
  template, always reporting the true `source`.
- `POST /api/v1/ml/explain` — IQR anomaly analysis + explanation.
- `scripts/setup_local_llm.sh` — install Ollama, pull a small GGUF model, and
  verify via `/api/tags` before claiming the model is loaded.
- `scripts/setup_android_workspace.sh` + `android/.../KeystoreHelper.java` —
  Android Studio workspace setup and the AndroidKeyStore public-key helper.
- `migrations/versions/0002_knowledge_base.py` — Alembic migration for the full
  knowledge base.
- `pyproject.toml` — ruff + pytest config; the CI lint gate now runs locally too.
