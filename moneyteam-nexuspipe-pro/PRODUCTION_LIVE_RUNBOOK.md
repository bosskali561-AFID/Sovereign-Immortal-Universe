# MONEYTEAM / NexusPipe Pro — Production Live Runbook

## Provider authorization

1. Create dedicated production provider credentials.
2. Grant only the scopes required for the selected workflow.
3. Never grant withdrawal/transfer capability to the automated trading service
   unless independently required.
4. Store secrets only in the deployment secret manager.

## Stripe

- Set `STRIPE_SECRET_KEY=sk_live_...`, `STRIPE_WEBHOOK_SECRET=whsec_...`, and
  `STRIPE_LIVE=true`.
- Register webhook endpoint: `POST /api/v1/providers/stripe/webhook`.
- Use the Stripe dashboard to select the required production events.
- Verify a signed webhook before processing it.

## Coinbase Advanced Trade

- Set production `COINBASE_API_KEY`, `COINBASE_API_SECRET`, and `COINBASE_LIVE=true`.
- Verify permissions using `GET /api/v1/providers/coinbase/health`.
- Use a dedicated trading credential with minimum required permissions.

## Database

- Use PostgreSQL in production. Run `alembic upgrade head`.
- Schedule `scripts/backup.sh` and retain backups according to your RPO/RTO policy.

## HTTPS / deployment

- Put the FastAPI service behind an HTTPS reverse proxy or managed HTTPS platform.
- Set `CORS_ORIGINS` and `TRUSTED_HOSTS` to the exact production domain.

## Monitoring

- Set `MONITORING_ENABLED=true` and `SENTRY_DSN` when Sentry is used.
- Monitor `/api/v1/health` and `/api/v1/readiness`, provider errors, webhook
  failures, reconciliation mismatches, latency, and 429/5xx rates.

## Live approval sequence

Keep `KILL_SWITCH=true` and `ALLOW_LIVE_EXECUTION=false` until all provider,
database, security, and monitoring checks pass. Then, during an authorized
maintenance window:

1. Verify `/api/v1/readiness`.
2. Verify provider health.
3. Verify webhook delivery.
4. Verify approval token.
5. Set `KILL_SWITCH=false`.
6. Set the selected mode (`FINANCIAL_MODE=live` and/or `TRADING_MODE=live`).
7. Set `ALLOW_LIVE_EXECUTION=true`.
8. Redeploy.
9. Re-run readiness.
10. Perform the smallest permitted live operation.
11. Confirm provider ID and receipt.
12. Reconcile against the provider dashboard.
13. Record the change in the audit log.

A provider operation without a validated provider ID/receipt must never be
reported as successful.
