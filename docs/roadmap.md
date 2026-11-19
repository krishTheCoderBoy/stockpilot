# Roadmap

Status: **done**, **partial**, **planned**.

The README's roadmap uses an older phase numbering. This file follows the numbering the project is actually being built in; the README roadmap should be aligned to it.

| # | Phase | Status |
|---|---|---|
| 1 | Core platform | partial |
| 2 | Production foundation | done |
| 3 | Event-driven architecture | done |
| 4 | Microservices | partial |
| 5 | Docker and hardening | partial |
| 6 | Search (PostgreSQL full-text) | done |
| 7 | Procurement intelligence | done |
| 8 | Operational AI | partial |

## 1. Core platform: partial

Done: dashboard (in inventory-service), auth + RBAC, products and categories, warehouses, inventory, movement ledger (now including `DAMAGED` and `RETURNED`), batches with expiry, reserved stock, suppliers, purchase orders with receiving, purchase-order cancellation and expected date.

Open:
- Tests. The only tests are the old monolith's in `backend/tests`; none exist for the services.
- Supplier `is_active` vs the spec's `status` (deliberately left as is).

## 2. Production foundation: done

Redis caching, rate limiting, RQ email worker (auth-service), security headers, and inventory-service's worker and scheduler for the expiry and low-stock / pending-PO notification jobs.

## 3. Event-driven architecture: done

RabbitMQ topic exchange, domain events, consumers with bounded retry, delay, DLQ and idempotency. Receipt events are best-effort (see [architecture.md](architecture.md)).

## 4. Microservices: partial

Done: auth, inventory and procurement services, gateway, database per service, one-off data copy from the shared database.

Open: remove the duplicated modules from `backend/` once data migration is verified everywhere; port its tests.

## 5. Docker and hardening: partial

Done: development `docker-compose.yml` and a Dockerfile per service and the frontend.

Open: add chatbot-service to the compose file, production images, secret management, TLS, health/readiness probes, CI, observability, and closing the receipt-event gap (transactional outbox).

## 6. Search: done

PostgreSQL `tsvector` search for products, warehouses, suppliers, purchase orders and movements, and live results in the command palette. Results open the matching list page (purchase orders open their detail page); there are no per-entity detail pages yet.

## 7. Procurement intelligence: planned

Done: demand-history endpoint, a rule-based reorder engine with explanations, statistical forecasting (moving average, exponential smoothing, Holt-Winters) chosen by backtest, risk flags and days of cover, draft POs from recommendations, and a Planning page with forecast charts plus dashboard cards.

Notes: demand is `ISSUE` movements only. Safety stock falls back to the product's reorder point because products have no separate safety-stock field. `scripts/seed_demand_history.py` backfills realistic history for development databases (it rewrites on-hand quantities, so it needs `--confirm`).

Open: tests; a forecast quality dashboard; per-supplier lead-time statistics.

## 8. Operational AI: planned

Built: `chatbot-service` (port 8004) with read tools over the public APIs, mutation tools that only prepare an action, signed single-use confirmation, a guarded Claude tool-use loop that degrades gracefully, and a chat slide-over in the frontend (Ctrl/⌘+J).

Status is partial: the loop has been run with a real model (Groq `openai/gpt-oss-120b`) against a fake backend, covering a read question, a prepared action that executed nothing, and a planted instruction that was ignored. It has not yet been run against the real stack, and the Claude path has not been run live.

Open: add chatbot-service to `docker-compose.yml` (Docker work is Phase 5), tests, streaming replies, per-user usage limits.
