# API

All requests go through the gateway (`http://localhost:8000`) or directly to a service (auth `:8001`, inventory `:8002`, procurement `:8003`). Each service serves Swagger at `/docs` outside production.

Authenticated endpoints need `Authorization: Bearer <access_token>`. A missing or invalid token returns 401; a valid token with the wrong role returns 403. Roles: `A` = ADMIN, `I` = INVENTORY_MANAGER, `P` = PROCUREMENT_MANAGER. Errors use FastAPI's `{"detail": "..."}` body. List endpoints take `skip` and `limit`.

Trailing slashes matter on collection routes: `/products/`, not `/products`.

## Auth service

| Method | Path | Access | Purpose |
|---|---|---|---|
| POST | `/auth/login` | public | Email + password. Returns a token, or `otp_required: true` after sending a code. |
| POST | `/auth/verify-login-otp` | public | Exchange the login code for a token. |
| POST | `/auth/resend-login-otp` | public | Send a new login code. |
| POST | `/auth/forgot-password` | public | Email a reset code. Same response whether or not the email exists. |
| POST | `/auth/reset-password` | public | Set a new password with the code. |
| POST | `/auth/forgot-username` | public | Email the username for an email or mobile number. Same response either way. |
| POST | `/users/` | A | Create a user (they must then verify with a code). |
| POST | `/users/verify-otp` | public | Verify a new account with the emailed code. |
| GET | `/users/me` | any role | Current user. |
| GET | `/internal/users/recipients?roles=ADMIN&roles=...` | `X-Internal-Token` | Active users' email addresses for the given roles. Service-to-service only; not routed by the gateway and hidden from Swagger. |

Public auth endpoints are rate limited (3 to 5 per minute in production).

## Inventory service

### Products and categories

| Method | Path | Access | Purpose |
|---|---|---|---|
| POST | `/products/` | A, I | Create a product. |
| GET | `/products/` | A, I, P | List products. |
| GET | `/products/search?q=&limit=` | A, I, P | Full-text search (ranked). |
| GET | `/products/{product_id}` | A, I, P | Get one. |
| PATCH | `/products/{product_id}` | A, I | Partial update. |
| POST | `/product-categories/` | A, I | Create a category. |
| GET | `/product-categories/` | A, I, P | List categories. |

### Warehouses

| Method | Path | Access | Purpose |
|---|---|---|---|
| POST | `/warehouses/` | A | Create. |
| GET | `/warehouses/` | A, I, P | List. |
| GET | `/warehouses/search?q=&limit=` | A, I, P | Full-text search. |
| GET | `/warehouses/{warehouse_id}` | A, I, P | Get one. |
| PATCH | `/warehouses/{warehouse_id}` | A | Partial update. |

### Stock

| Method | Path | Access | Purpose |
|---|---|---|---|
| GET | `/inventory/` | A, I, P | Stock rows. |
| GET | `/inventory/low-stock?limit=` | A, I, P | Stock rows whose available quantity is at or below the product's reorder point. |
| GET | `/inventory/product/{product_id}` | A, I, P | Stock for a product across warehouses. |
| GET | `/inventory/warehouse/{warehouse_id}` | A, I, P | Stock in a warehouse. |
| GET | `/inventory/{product_id}/{warehouse_id}` | A, I, P | One stock row. |

Each row has `on_hand_quantity`, `reserved_quantity` and `available_quantity` (= on hand − reserved), plus `average_unit_cost`.

### Movements

| Method | Path | Access | Purpose |
|---|---|---|---|
| POST | `/inventory-movements/` | A, I | Record a movement. |
| POST | `/inventory-movements/transfer` | A, I | Move stock between warehouses (two linked movements, one transaction). |
| GET | `/inventory-movements/` | A, I, P | Recent movements, newest first. |
| GET | `/inventory-movements/search?q=&limit=` | A, I, P | Full-text search over notes, plus movements of matching products or warehouses. |
| GET | `/inventory-movements/demand-history` | A, I, P | Outbound demand per day or week, aggregated in SQL. Filters: `product_id`, repeatable `product_ids`, `warehouse_id`, `date_from`, `date_to` (default last 180 days, max 731), `bucket=day\|week`. Only `ISSUE` counts as demand; transfers, write-offs and adjustments do not. Days without sales are absent (callers zero-fill). |
| GET | `/inventory-movements/product/{product_id}` | A, I, P | By product (`skip`, `limit`). |
| GET | `/inventory-movements/warehouse/{warehouse_id}` | A, I, P | By warehouse. |

`movement_type`: `RECEIVE`, `ISSUE`, `ADJUSTMENT_INCREASE`, `ADJUSTMENT_DECREASE`, `DAMAGED`, `RETURNED` (transfers create `TRANSFER_IN` / `TRANSFER_OUT`). Stock-out types fail with 400 when available stock is too low. `quantity` must be positive. An `ISSUE` may include `reservation_id` to consume a reservation.

### Reservations

| Method | Path | Access | Purpose |
|---|---|---|---|
| POST | `/stock-reservations/` | A, I | Reserve stock; 400 if available stock is insufficient. |
| GET | `/stock-reservations/` | A, I, P | List; filters `product_id`, `warehouse_id`, `status`. |
| GET | `/stock-reservations/{id}` | A, I, P | Get one. |
| POST | `/stock-reservations/{id}/release` | A, I | Release an `ACTIVE` reservation. |

### Batches

| Method | Path | Access | Purpose |
|---|---|---|---|
| GET | `/inventory-batches/product/{product_id}` | A, I, P | Batches for a product. |
| GET | `/inventory-batches/expiring?days=7` | A, I, P | Batches expiring within N days. |

### Dashboard

| Method | Path | Access | Purpose |
|---|---|---|---|
| GET | `/dashboard/summary` | A, I, P | Active products, inventory value (on hand × cost), low-stock count (available ≤ reorder point) and `pending_purchase_orders`. The last is fetched from procurement with the caller's token and is `null` if procurement is unreachable. |
| GET | `/dashboard/inventory-trend?months=6` | A, I, P | Stock in / stock out per month. |
| GET | `/dashboard/recent-movements?limit=5` | A, I, P | Latest movements with product and warehouse names. |
| GET | `/dashboard/notifications` | A, I, P | Low-stock items, plus a line for purchase orders awaiting approval when procurement is reachable. |

## Procurement service

| Method | Path | Access | Purpose |
|---|---|---|---|
| POST | `/suppliers/` | A, P | Create a supplier. |
| GET | `/suppliers/` | A, I, P | List. |
| GET | `/suppliers/search?q=&limit=` | A, I, P | Full-text search (name, code, contact). |
| GET | `/suppliers/{supplier_id}` | A, I, P | Get one. |
| PATCH | `/suppliers/{supplier_id}` | A, P | Partial update. |
| POST | `/purchase-orders/` | A, P | Create a draft PO. Supplier, warehouse and products are validated; accepts optional `expected_date`. |
| GET | `/purchase-orders/` | A, I, P | List; optional `status` filter. |
| GET | `/purchase-orders/by-number/{po_number}` | A, I, P | Exact lookup by PO number. |
| GET | `/purchase-orders/search?q=&limit=` | A, I, P | Full-text search (PO number, notes). |
| GET | `/purchase-orders/summary` | A, I, P | `pending_count` and `awaiting_approval_count`; used by inventory's dashboard. |
| GET | `/purchase-orders/{po_id}` | A, I, P | Get one with its items. |
| POST | `/purchase-orders/{po_id}/submit` | A, P | DRAFT → SUBMITTED |
| POST | `/purchase-orders/{po_id}/approve` | A | SUBMITTED → APPROVED |
| POST | `/purchase-orders/{po_id}/mark-ordered` | A, P | APPROVED → ORDERED |
| POST | `/purchase-orders/{po_id}/receive` | A, P | Record received quantities; moves to PARTIALLY_RECEIVED or RECEIVED. |
| POST | `/purchase-orders/{po_id}/close` | A, P | RECEIVED → CLOSED |
| POST | `/purchase-orders/{po_id}/cancel` | A | Cancel from DRAFT, SUBMITTED, APPROVED or ORDERED. 400 once anything has been received. |

An illegal status change returns 400 (`Cannot transition from X to Y`). Receiving more than the remaining quantity returns 400.

## Planning (procurement service)

Reorder recommendations and demand forecasts. Planning never reads inventory's database: it calls inventory-service with the caller's own token (a 503 is returned if inventory is unreachable). Read access is `A, I, P`; creating a draft PO is `A, P`.

| Method | Path | Purpose |
|---|---|---|
| GET | `/planning/recommendations` | Paginated (`skip`, `limit` up to 200). Filters: `risk` (`OK`, `LOW`, `STOCKOUT_RISK`), `supplier_id`, `warehouse_id`; `mode=auto` (statistical model) or `rules` (simple average). Most urgent first. |
| GET | `/planning/recommendations/{product_id}` | One product, optionally for one `warehouse_id`. |
| GET | `/planning/summary` | Counts: products, recommended purchases, and per risk level. Used by the dashboard cards. |
| GET | `/planning/forecast/{product_id}` | Recent daily history plus a daily forecast with an 80% band, the model used and why, backtest error and history length. Optional `warehouse_id`, `horizon_days`. |
| POST | `/planning/recommendations/{product_id}/draft-po` | Body `{warehouse_id, quantity?}`. Recomputes the recommendation server-side, then creates a DRAFT PO through the normal PO service (supplier, warehouse and product are validated as usual). |

Each recommendation carries every input and a readable explanation, for example *"Current available = 42, Incoming = 20, Safety stock = 30, Forecast demand = 160, Recommended order = 148"*, a `reasons` list, `risk`, `days_of_cover`, `lead_time_days` with its source (supplier or default) and the model used.

## Chatbot service

Reached through the gateway at `/chat`. The caller's JWT is required and is forwarded unchanged to every business API the assistant calls, so the assistant can never do more than the user.

| Method | Path | Purpose |
|---|---|---|
| POST | `/chat` | Body `{message, conversation_id?}`. Returns `{reply, tool_calls[], pending_action?, conversation_id}`. Rate limited (10/min in production). |
| POST | `/chat/confirm` | Body `{token}`. Executes a prepared action, once, and returns the business API's result or its error message verbatim. Repeating it returns the stored outcome. Rate limited (20/min in production). |

`pending_action` is `{token, tool, summary, details, expires_at}`. Tokens are signed, bound to the user and the exact endpoint and body, valid for 5 minutes, and single-use. If the model provider is down or not configured, `/chat` still answers 200 with a plain explanation.

## Health

`GET /internal/purchase-orders/summary` (procurement) and `GET /internal/users/recipients` (auth) are service-to-service only: they need the `X-Internal-Token` header, are hidden from Swagger and are not routed by the gateway.

Every service and the gateway expose `GET /health`.
