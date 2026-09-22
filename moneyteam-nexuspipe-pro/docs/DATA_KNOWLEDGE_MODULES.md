# MONEYTEAM / NexusPipe Pro — Data, Knowledge & Configuration Modules (v4.3)

**Package:** MONEYTEAM_NexusPipe_Pro_LIVE_PRODUCTION v4.3 · **Status:** verified (13/13 tests, lint clean) · **Mode:** offline / paper by default

This document describes the data, knowledge, and configuration modules added to the project structure, how they integrate, and the invariants they enforce.

---

## 1. Configuration module — `app/config.py`

Central typed settings via `pydantic-settings` (`Settings` + `get_settings()` lru-cached singleton).

**Safety defaults (enforced by validators and the live gate):**

| Setting | Default | Meaning |
|---|---|---|
| `TRADING_MODE` | `paper` | no live trading |
| `FINANCIAL_MODE` | `sandbox` | no live money movement |
| `ALLOW_LIVE_EXECUTION` | `false` | provider execution blocked |
| `KILL_SWITCH` | `true` | global stop |
| `REQUIRE_HUMAN_APPROVAL` | `true` | single-use live approval token required |
| `REQUIRE_AUTH` | `true` | admin token on all mutating routes |
| `LOCAL_LLM_ENABLED` | `false` | offline-first; no network call unless enabled |

Validators reject any value other than paper/live and sandbox/live for the mode fields.

**Safe config API:** `GET /api/v1/config` (admin) returns the full settings dump with every secret-looking key redacted to `[REDACTED]` (via `app/services/payload.py`).

---

## 2. Data models — `app/models.py` (SQLAlchemy 2.0, typed `Mapped[]`)

**Operational tables:**

| Table | Purpose |
|---|---|
| `receipts` | provider execution receipts with SHA-256 evidence hashes |
| `transactions` | sandbox transaction history |
| `webhook_events` | signed webhook events, unique `event_id` (dedupe) |
| `runs` | cycle run records |
| `settings` | key/value app settings |
| `audit_events` (`app/services/audit.py`) | append-only audit trail |

**Knowledge base (additive — append-only, never deleted):**

| Table | Fields |
|---|---|
| `signals_raw` | `source`, `payload` (JSON), `created_at` |
| `opportunities` | `symbol`, `ept`, `action`, `phase`, `status`, `payload` |
| `winners` | `symbol`, `pnl_paper`, `strategy_dna` (JSON) |
| `failures` | `symbol`, `reason`, `autopsy` (JSON) |

Migrations: `migrations/versions/0001_initial.py` (webhook_events) and `0002_knowledge_base.py` (full knowledge base + audit events). `alembic upgrade head` applies them; `Base.metadata.create_all()` also bootstraps dev SQLite.

---

## 3. Knowledge service — `app/services/knowledge.py`

Append-only store with helpers:

- `record_signal` / `record_opportunity` / `record_winner` / `record_failure` — each writes and commits one row; nothing is ever updated or deleted.
- `summary(db)` — counts per table plus `policy: append_only_never_deleted`.
- `recent_opportunities(db, limit)` — newest first, capped at 500.
- `leaderboard(db, limit)` — winners ranked by paper P&L.

The system learns from full history: every signal (win or lose) is retained for autopsy and strategy-DNA analysis.

---

## 4. Six-phase L.S.P.A. engine — `app/services/lspa.py`

`run_lspa_cycle(db, seed=42, top_n=2)` executes:

1. **Intake** — deterministic seeded signals (3 symbols), each stored in `signals_raw` with its full IQR analysis.
2. **Plan** — EPT scoring `Profit² / (Effort × Task)`; each candidate stored in `opportunities`.
3. **Delegate** — honest agent availability: probes the local LLM runtime with real telemetry (`llm_source: disabled | unreachable | ollama`), falls back to classical deterministic logic.
4. **Execute** — paper trades only; winners/failures recorded with strategy DNA / autopsy.
5. **Verify** — consensus gate (paper-mode check, no-live-side-effects, stop-loss respected, payload bounds), reported as `n/4`.
6. **Report** — full JSON telemetry (request_id, runtime, plan, risks, verification, user_summary) plus a natural-language anomaly explanation whose `source` is honestly reported.

CLI: `scripts/run_lspa_cycle.py [seed] [top_n]` · API: `POST /api/v1/lspa/cycle` (admin).

---

## 5. Local-LLM explanation engine — `app/services/local_llm.py`

Offline-first Ollama integration:

- `local_llm_status()` — probes `{LOCAL_LLM_URL}/api/tags`; never claims a model is loaded without this telemetry.
- `explain_anomalies(analysis)` — uses local Ollama chat when enabled *and* reachable; otherwise a deterministic template explanation. The `source` field (`ollama` | `template`) always states which engine produced the text — no fabricated LLM output.
- Setup: `scripts/setup_local_llm.sh` (installs Ollama, pulls the GGUF model, verifies via `/api/tags` before claiming success).
- API: `POST /api/v1/ml/explain` — IQR analysis (`app/services/ml_checker.py`) + explanation.

---

## 6. Supporting modules

- `app/services/payload.py` — recursive secret redaction (`[REDACTED]`) for keys containing password/secret/token/api_key/authorization/credential.
- `app/services/ml_checker.py` — IQR anomaly detection (Q1/Q3/fences/severity, `sample_count`).
- `app/services/audit.py` — append-only audit events (`audit(db, event_type, detail, actor)`).
- `app/services/receipts.py` — persistent receipts with SHA-256 evidence hashes: **no verified receipt = no claimed execution**.

## 7. API surface (data/knowledge/config)

| Route | Auth | Purpose |
|---|---|---|
| `POST /api/v1/lspa/cycle` | admin | run six-phase cycle |
| `GET /api/v1/config` | admin | redacted settings view |
| `GET /api/v1/knowledge/summary` | — | table counts + policy |
| `GET /api/v1/knowledge/opportunities` | — | recent opportunities |
| `GET /api/v1/knowledge/leaderboard` | admin | winners by P&L |
| `POST /api/v1/ml/check` | — | IQR anomaly check |
| `POST /api/v1/ml/explain` | — | IQR + explanation (source reported) |

## 8. Invariants

1. No verified provider receipt = no claimed execution.
2. No model load is ever claimed without telemetry evidence.
3. Knowledge base is append-only; history is never rewritten.
4. Offline/paper defaults require explicit, audited human action to change (see `PRODUCTION_LIVE_RUNBOOK.md`).
