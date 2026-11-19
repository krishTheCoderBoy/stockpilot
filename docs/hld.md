# High-Level Design

## 1. Purpose

StockPilot tracks physical stock across warehouses and drives replenishment through purchase orders. Users: administrators, inventory managers and procurement managers, with different permissions on the same data.

Core questions it answers: how much of each product is where, how much of it is actually available, what is on order, and what needs reordering.

## 2. Context

```text
Browser (React SPA) ──► Gateway ──► auth-service        ──► auth_db
                                ├─► inventory-service   ──► inventory_db
                                └─► procurement-service ──► procurement_db
                                         ▲        │
                         RabbitMQ events ┘        └──► Redis (cache, rate limit, queues)
                                  SMTP ◄── email jobs (OTP, alerts)
```

External dependencies: PostgreSQL, Redis, RabbitMQ, an SMTP server. Redis, RabbitMQ and SMTP failures degrade features (caching, events, email); they do not take the API down.

## 3. Components

| Component | Responsibility |
|---|---|
| Frontend | Pages for products, warehouses, stock, movements, suppliers, purchase orders, profile, plus login/OTP flows. TanStack Query for data; one axios client per service. |
| Gateway | Route requests to the owning service by path prefix. No business logic or auth. |
| auth-service | Registration (admin-created users), login with email OTP, JWT issue, password and username recovery. Internal recipients lookup for other services. |
| inventory-service | Catalogue, warehouses, stock levels, the movement ledger, batches and expiry, stock reservations, low-stock alerts, event consumers. |
| procurement-service | Suppliers and the purchase-order lifecycle, including receiving and cancellation. Publishes events. |
| shared | JWT verification and role checks used by every service; the one-off data copy tool. |

Each service is independently deployable and owns its database. Cross-service identifiers are plain UUIDs (see [database.md](database.md)).

## 4. Key flows

**Login.** Password check → emailed one-time code (required again after 30 days) → JWT with user id and role. Services verify the JWT locally.

**Stock movement.** A manager records a movement. Stock rows are locked, the change is checked against *available* stock, the ledger row and the new quantities are saved in one transaction, then an `InventoryUpdated` event and, if available stock is at or below the reorder point, a `StockLow` event are published.

**Reservation.** A hold reduces available stock without changing on-hand stock. It is released explicitly, or consumed by an `ISSUE` that references it.

**Procurement.** Draft → submitted → approved (admin) → ordered → received (partly or fully) → closed; or cancelled before any receipt. Creating a PO checks the supplier locally and the warehouse and products through inventory-service.

**Receiving.** Procurement commits received quantities, then publishes a receipt event. Inventory's consumer turns it into `RECEIVE` movements, which also create batches and update average cost.

**Alerts.** `StockLow` and `PurchaseOrderApproved` events trigger emails to admins and inventory managers (recipients fetched from auth-service).

## 5. Data

PostgreSQL, one database per service, Alembic migrations per service. Money and quantities are `NUMERIC`. The movement table is an append-only ledger; stock levels are the running result of it. Details: [database.md](database.md).

## 6. Cross-cutting concerns

| Concern | Approach |
|---|---|
| Authentication | JWT (HS256) shared secret; OTP on login. |
| Authorization | Role strings in the JWT, checked per endpoint by `require_role`. |
| Consistency | ACID inside a service. Across services: HTTP validation on write, events for propagation, idempotent consumers. |
| Resilience | Event publish and cache failures are logged and skipped. Consumers retry 3 times with a delay, then dead-letter. |
| Concurrency | Row locks on stock rows; fixed lock order for transfers and for stock-then-reservation. |
| Performance | Redis caching and indexed queries; GIN indexes for full-text search. |
| Security | Rate-limited public auth routes, security headers, CORS restricted to the frontend origin, internal endpoints behind a token and unrouted by the gateway. |

## 7. Known limitations

- A receipt event is published after the procurement commit; if the broker is down then, stock does not move. Accepted for now.
- JWTs are not revocable: a deactivated user stays valid until the token expires.
- One symmetric secret signs and verifies tokens in every service.
- Reservations do not expire.
- No automated tests exist for the services.
- Development Docker setup only; not hardened.

## 8. Decisions

| Decision | Why |
|---|---|
| Database per service, no cross-DB foreign keys | Services can change and deploy on their own; the cost is application-level validation. |
| Local JWT verification | No auth-service call on the hot path, no single point of failure per request. |
| Events best-effort over a transactional outbox | Simpler; the gap above is the accepted trade-off. |
| Reservations as rows plus a running counter | An audit trail and safe release, with a cheap read of available stock. |
| `DAMAGED` / `RETURNED` as their own movement types | Forecasting needs real demand (`ISSUE`) separated from write-offs and returns. |
| Gateway as a dumb proxy | Keeps authorization in the service that owns the data. |
