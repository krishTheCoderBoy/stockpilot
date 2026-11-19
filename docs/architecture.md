# Architecture

StockPilot began as a modular monolith (`backend/`, kept for reference and as the source of the original data) and is now split into services behind a gateway.

## Service map

```text
                    ┌───────────────────────┐
                    │  React (Vite, :5173)  │
                    └───────────┬───────────┘
                                │ HTTP (VITE_API_GATEWAY_BASE_URL)
                    ┌───────────▼───────────┐
                    │   Gateway (:8000)     │  routes by first path segment
                    └───┬───────────┬───────┴──────┐
                        │           │              │
              ┌─────────▼──┐  ┌─────▼────────┐  ┌──▼───────────────┐
              │ auth-svc   │  │ inventory-svc│  │ procurement-svc  │
              │   :8001    │  │    :8002     │  │      :8003       │
              └─────┬──────┘  └──┬───────┬───┘  └──┬───────────┬───┘
                    │            │       │         │           │
                 auth_db   inventory_db  │    procurement_db   │
                                         │                     │
                                   ┌─────▼─────────────────────▼─────┐
                                   │ RabbitMQ (topic: stockpilot.events) │
                                   └─────────────────────────────────┘
                 Redis: cache, rate limits, RQ queues, consumer dedup
```

| Service | Port | Owns | Notes |
|---|---|---|---|
| gateway | 8000 | nothing | Plain reverse proxy. No auth logic; services verify JWTs themselves. |
| auth-service | 8001 | users, OTPs | Issues JWTs. Sends OTP and username emails through an RQ worker. |
| inventory-service | 8002 | products, warehouses, stock, movements, batches, reservations | Runs the event consumers. |
| procurement-service | 8003 | suppliers, purchase orders | Publishes purchase-order events. |
| chatbot-service | 8004 | nothing | Stateless assistant. Calls the Claude API and the business APIs (through the gateway, with the user's token). Optional short conversation history in Redis. |
| shared | n/a | n/a | Python package (`services/shared`) with JWT verification, `require_role`, and the data-copy tool. |

## Gateway

Routing is by the first path segment:

| Prefix | Service |
|---|---|
| `auth`, `users`, `otp` | auth |
| `products`, `product-categories`, `warehouses`, `inventory`, `inventory-movements`, `inventory-batches`, `stock-reservations`, `dashboard` | inventory |
| `suppliers`, `purchase-orders`, `planning` | procurement |
| `chat` | chatbot |

Search endpoints (`/products/search`, ...) follow their resource. `/internal/*` is deliberately not routed, so service-to-service endpoints cannot be reached from a browser. In the frontend, setting `VITE_API_GATEWAY_BASE_URL` points the three axios clients (`authApi`, `inventoryApi`, `procurementApi`) at the gateway; unset, each uses its own service URL.

The dashboard is served by inventory-service. Its pending-PO figure comes from procurement over HTTP and is `null` when procurement is down.

## Auth model

- Login is email + password, then a one-time code (OTP) by email. The OTP is only required again after 30 days.
- The access token is an HS256 JWT with `sub` (user id) and `role`. Roles: `ADMIN`, `INVENTORY_MANAGER`, `PROCUREMENT_MANAGER`.
- Every service verifies the token locally with the shared `SECRET_KEY`; no service calls auth-service per request. Consequence: a deactivated user keeps a valid token until it expires (60 minutes by default).
- Authorization uses `require_role("ADMIN", ...)` with plain uppercase strings read from the token. Only auth-service has a `UserRole` enum, because only it owns `users`.
- User creation (`POST /users/`) is admin-only.
- Service-to-service calls that need user data use an internal endpoint (`GET /internal/users/recipients` on auth-service) guarded by an `X-Internal-Token` shared secret. It is not routed by the gateway.

## Communication

**Synchronous (HTTP).** procurement → inventory at PO creation, to confirm the warehouse and products exist (the caller's own token is forwarded). inventory → auth for notification recipients.

**Asynchronous (RabbitMQ).** One durable topic exchange, `stockpilot.events`; routing key = event type. Events are published best-effort: a broker failure is logged and never breaks the request.

| Event | Published by | Consumed by |
|---|---|---|
| `PurchaseOrderCreated` | procurement | nobody yet |
| `PurchaseOrderApproved` | procurement | inventory notification consumer (email) |
| `PurchaseOrderCancelled` | procurement | nobody yet |
| `ReceivePurchaseOrderItems` | procurement | inventory receipt consumer (applies stock) |
| `PurchaseOrderReceived` | procurement | nobody yet |
| `InventoryUpdated` | inventory | nobody yet |
| `InventoryTransferred` | inventory | nobody yet |
| `StockLow` | inventory | inventory notification consumer (email) |

### Receiving stock

```text
POST /purchase-orders/{id}/receive           (procurement)
  1. update received quantities + PO status, commit
  2. publish ReceivePurchaseOrderItems         (best-effort)
        │
        ▼
inventory receipt consumer
  3. for each line: RECEIVE movement, update stock, create batch
  4. commit once; then record the event id in Redis
```

Known limitation: step 2 happens after step 1's commit. If RabbitMQ is down at that moment, the PO shows received but stock never moves. This was reviewed and accepted for now; a transactional outbox is the standard fix if it needs closing.

### Consumers

Both inventory consumers share one retry helper (`app/consumers/retry.py`): up to 3 retries with a 5 second delay via a per-consumer `.retry` queue, then a per-consumer `.dlq`. The dedup key is written only after success; if Redis is down, processing continues without the duplicate check.

## Background jobs

inventory-service runs an RQ worker (`worker.py`) and a scheduler (`scheduler.py`) on a `notifications` queue:

| Job | Schedule | What it does |
|---|---|---|
| `scan_and_notify_expiring_batches` | hourly | Emails admins and inventory managers about batches expiring within 7 days. |
| `scan_and_notify_low_stock_and_pending_pos` | daily | Emails low-stock items and POs awaiting approval. |

Recipients come from auth-service; PO counts come from procurement through its internal endpoint (jobs have no user token). If either is unreachable the run is skipped or the PO line is left out, and the next tick tries again. The scheduler must run as exactly one process; it re-registers the jobs on every start so restarts do not duplicate them.

## Planning (Phase 7)

procurement-service owns suppliers and their `lead_time_days`, so it also owns the reorder engine (`app/modules/planning`). It needs stock and demand data from inventory, which it fetches over HTTP with the caller's token and caches briefly in Redis (shared across users, 60 seconds, failures ignored). It never reads `inventory_db`; if inventory is unreachable the planning endpoints return 503 and nothing else is affected.

```text
inventory-service                              procurement-service (planning)
  /inventory, /products  ─────────────────►  clients.py   (HTTP + cache)
  /inventory-movements/demand-history ────►        │
                                                   ▼
                                  forecasting.py  (daily series → forecast + band)
                                                   │ forecast_demand
                                                   ▼
open POs (procurement DB) ───────────────►  rules.py  (pure: available, incoming, safety,
                                                     forecast → order, risk, cover)
                                                   │
                                                   ▼
                                     service.py  (explanation, reasons, caching)
```

- **The rule** is a pure function: `recommended = max(0, forecast_demand + safety_stock − available − incoming)`, rounded up to the product's order multiple. The forecast is only an input, so replacing the forecaster never touches the rules.
- **Inputs:** available = on hand − reserved; incoming = ordered − received on APPROVED, ORDERED and PARTIALLY_RECEIVED POs (SUBMITTED is excluded, since it can still be rejected); safety stock = the inventory record's override, else the product's reorder point (products have no separate safety-stock field); lead time = the default supplier's, else a configured default (7 days), and the explanation says which.
- **Demand** is `ISSUE` movements only. `TRANSFER_OUT`, `DAMAGED` and `ADJUSTMENT_DECREASE` are not demand, which is why they are separate movement types.
- **Forecasting** (`mode=auto`): moving average (baseline), simple exponential smoothing, and Holt-Winters with weekly seasonality (statsmodels). The last 14 days are held out and each model is scored by MAE (MAPE is reported); a model is used only if it beats the baseline by at least 5%. With under 28 days of history, or no sales, the baseline is used and the reason says so. The band is residual-based (80%). Results are cached per product for 30 minutes and keyed by date.
- **Risk:** `STOCKOUT_RISK` when available plus incoming will not last through the lead time at the recent daily demand; `LOW` when an order is recommended; otherwise `OK`.
- **Draft POs** go through `PurchaseOrderService.create_po`; planning never writes around it.

## Chatbot (Phase 8)

```text
Browser ─► gateway ─► chatbot-service ─► Claude API
                           │  tool calls (JWT forwarded)
                           ▼
                        gateway ─► inventory / procurement APIs (RBAC enforced there)
```

- **No database, no models.** The service has no DB connection and imports nothing from other services. Redis holds only optional conversation history (keyed by user and conversation id, one hour).
- **Tools are thin HTTP clients** for existing public endpoints: search, stock levels, low stock, PO lookup and list, recommendations, stockout risk, forecasts and movement history. Results are trimmed before they reach the model and presented as `untrusted_data`; the system prompt tells the model to ignore instructions found inside them. Errors (403, 404, timeouts) come back as plain messages. Each turn is capped (8 tool calls, 10 model calls).
- **Mutations never run from the model.** Mutation tools only validate and return a pending action. The UI shows a confirmation card; only `POST /chat/confirm` executes, calling the same endpoints the UI uses (receive, submit, approve, mark-ordered, cancel, record a movement, create a draft PO from a recommendation).
- **Confirmation tokens** are HMAC-signed with a dedicated key, expire after 5 minutes, bind the user, endpoint and body, and are limited to a whitelist of business endpoints. A Redis marker makes them single-use; repeating a confirmation returns the stored outcome. If Redis is down the action is not confirmable (it fails closed, nothing runs).
- **Model providers** sit behind one small interface: Anthropic (Claude) through its SDK, and any OpenAI-compatible API (Groq, xAI) over HTTP. `LLM_PROVIDER=auto` uses `ANTHROPIC_API_KEY` if set, otherwise `GROK_API_KEY`, recognised by prefix (`gsk_` Groq, `xai-` xAI) and only ever sent to that provider's official endpoint. On providers with a small token budget the service offers only the read tools unless the message sounds like an action, caps tool-result size, and retries rate limits with a short wait.
- **Model provider failures** (no key, bad key, rate limit, timeout, outage) produce a friendly 200 reply, never a 500. Replies are cleaned to plain text, because the chat window does not render markdown.
- Tool calls are logged by name, arguments, status and latency; tokens and response bodies are not.

## Stock rules

- `on_hand` changes only through the movement ledger. Reservations change `reserved`, never `on_hand`.
- Available = on hand − reserved, defined once in `Inventory.available_quantity`. Stock-out movements are limited by available stock, and low-stock alerts compare available stock to the reorder point.
- Stock rows are locked (`SELECT ... FOR UPDATE`) while a movement or reservation is applied.

## Layering

Inside each service: `routes.py` → `service.py` → `repository.py` → `models.py` / `schemas.py`. Routes hold no business logic. Repositories `flush()`; services own `commit()` / `rollback()`. State machines are explicit `dict[Status, set[Status]]` maps. Redis, RabbitMQ and other external-call failures degrade gracefully.

## Runtime

`docker compose up --build` starts the whole stack for development (see the README). Background pieces: auth email worker (RQ), inventory receipt consumer, inventory notification consumer, inventory worker and scheduler.
