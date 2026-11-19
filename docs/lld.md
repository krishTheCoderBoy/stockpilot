# Low-Level Design

## 1. Code layout

```text
services/
  shared/auth/dependencies.py     JWT decode, CurrentUser, require_role
  shared/migrations/copy_data.py  one-off copy of a service's tables from the old shared DB
  gateway/app/main.py             prefix → upstream proxy
  auth-service/main.py            (app/ modules: auth, users, otp)
  inventory-service/app/          modules: products, warehouses, inventory, inventory_movements,
                                  inventory_batches, inventory_reservations
                                  consumers/, jobs/, core/
  procurement-service/app/        modules: suppliers, purchase_orders; core/
```

Each module follows `routes.py → service.py → repository.py → models.py / schemas.py`:

- **routes**: HTTP only. Declares `response_model`, the `require_role(...)` dependency and calls one service method.
- **service**: business rules, transactions (`commit` / `rollback`), event publishing.
- **repository**: queries; `flush()` only, never `commit()`. Row locks via `for_update=True`.
- **schemas**: separate Create / Update / Out Pydantic models. ORM objects are never returned.

No repository commits. Services call `commit()` / `rollback()`; `OtpService.verify` is the one deliberate exception that leaves the commit to its caller, so a login code is consumed together with the change it authorises.

## 2. Authorization

```python
require_role("ADMIN", "INVENTORY_MANAGER")   # from shared.auth.dependencies
```

Reads `sub` and `role` from the JWT and compares the role against the allowed strings. Routers define `READ_ROLES` / `WRITE_ROLES` tuples. Auth-service uses its own `require_role` that loads the user (it owns `users`).

## 3. State machines

Both are explicit maps; `_transition` rejects anything not in the map with a 400.

**Purchase order** (`procurement_service/.../service.py`)

```python
ALLOWED_TRANSITIONS: dict[POStatus, set[POStatus]] = {
    DRAFT:              {SUBMITTED, CANCELLED},
    SUBMITTED:          {APPROVED, DRAFT, CANCELLED},
    APPROVED:           {ORDERED, CANCELLED},
    ORDERED:            {PARTIALLY_RECEIVED, RECEIVED, CANCELLED},
    PARTIALLY_RECEIVED: {RECEIVED},
    RECEIVED:           {CLOSED},
    CLOSED:             set(),
    CANCELLED:          set(),
}
```

`cancel()` additionally refuses any PO whose items have `received_quantity > 0`. `receive()` is allowed only from `ORDERED` / `PARTIALLY_RECEIVED`, and each line is limited to its remaining quantity.

**Reservation** (`inventory_reservations/service.py`)

```python
ACTIVE: {RELEASED, FULFILLED};  RELEASED: set();  FULFILLED: set()
```

## 4. Movement algorithm (`MovementService._apply_single_movement`)

1. Reject non-positive quantity. A `reservation_id` is allowed only on `ISSUE`.
2. Lock the stock row (`get_or_create(..., for_update=True)`); then lock the reservation, if any.
3. **Increase types** (`RECEIVE`, `ADJUSTMENT_INCREASE`, `TRANSFER_IN`, `RETURNED`): add to `on_hand`. `RECEIVE` also recalculates the weighted average cost when a unit cost is given and creates a batch.
4. **Decrease types** (`ISSUE`, `ADJUSTMENT_DECREASE`, `TRANSFER_OUT`, `DAMAGED`): require `available + own reservation >= quantity`, then subtract from `on_hand`. `ISSUE` and `DAMAGED` consume batches by soonest expiry.
5. If a reservation is being fulfilled: mark it `FULFILLED`, subtract its whole quantity from `reserved`, record the issued quantity and movement id. The unissued remainder becomes available again.
6. Add the ledger row, publish `InventoryUpdated`, and `StockLow` if `available <= reorder_point`.
7. The caller (`create_movement`, `transfer_stock`, or the receipt consumer) commits once.

Transfers lock both stock rows in sorted warehouse-id order before applying the out and in movements, so two opposite transfers cannot deadlock.

Lock order everywhere: stock row, then reservation.

Database backstops: `CHECK (reserved_quantity >= 0)` and `CHECK (reserved_quantity <= on_hand_quantity)`.

## 5. Consumers (`inventory-service/app/consumers`)

`retry.handle_delivery(channel, method, properties, body, queue_name, process)` wraps a `process(event: dict)` function.

```text
parse JSON ── fail ──► DLQ
check Redis "processed_event:{queue}:{event_id}" ── seen ──► ack
process(event)
   ├─ ok   ──► set Redis key (24h) ──► ack
   └─ fail ──► retries < 3 ? publish to <queue>.retry (TTL 5s, dead-letters back to <queue>) + ack
                         else publish to <queue>.dlq + ack
```

If Redis is unavailable the duplicate check is skipped. If a retry or DLQ publish itself fails, the message is nacked with requeue so it is not lost.

| Queue | Binds | Handler |
|---|---|---|
| `inventory.purchase-order-receipts` | `ReceivePurchaseOrderItems` | One `RECEIVE` movement per line, single commit |
| `notifications.consumer` | `StockLow`, `PurchaseOrderApproved` | Email recipients from auth-service; a failed lookup triggers a retry |

## 6. Search

`products`, `warehouses`, `suppliers`, `purchase_orders` and `inventory_movements` have a generated `search_vector` (weighted `to_tsvector('english', ...)`). Repositories run `search_vector @@ websearch_to_tsquery('english', q)` ordered by `ts_rank`. The `/search` route is declared before `/{id}` in the router so it is not captured as an id. The SQL expression lives in one constant per model and must match its migration. Movements are searched by their own notes OR by a matching product or warehouse (subqueries on those tables' vectors), so product and warehouse text is never copied into the ledger; notes matches rank first, the rest by newest.

## 7. Migrations

- `0001` per service is explicit DDL, not `create_all()`.
- Search-vector migrations check `pg_attribute.attgenerated`, so they work on a fresh database and on one created by an older revision.
- Adding an enum value: `ALTER TYPE ... ADD VALUE IF NOT EXISTS` inside `op.get_context().autocommit_block()`.
- Revision chains: auth `0001`; inventory `0001 → 832942e4a3ce → 7d896323cfb5 → b3f5a7c91d24 → d5b9e3f72a48 → e6c1f4a83b59 → f7d2a9c15e80`; procurement `0001 → 8e1439173f7e → 016daf889d2f → c4a8d2e61f37`.

## 8. Dashboard and jobs

`DashboardService` (inventory) reads only inventory tables through `DashboardRepository`. The inventory part of the summary is cached in Redis for 60 seconds under `dashboard:summary` (invalidated by movements, reservations and receipts), while the pending-PO figure is fetched fresh through `app/core/procurement_client.py` and never cached. Jobs in `app/jobs/notification_jobs.py` are scheduled by `scheduler.py` onto the queue that `worker.py` consumes.

## 9. Frontend

`src/lib/api.ts` creates `authApi`, `inventoryApi` and `procurementApi` (all with the bearer-token and 401 interceptors). When `VITE_API_GATEWAY_BASE_URL` is set, all three use it as their base URL. Server state uses TanStack Query; types are in `src/lib/queries.ts`. Pages live in `src/pages/<area>`. The command palette (`components/ui/CommandPalette.tsx`) runs one debounced TanStack Query per entity against the `/search` endpoints, so one failing service only empties its own group.

## 10. Error handling

| Situation | Behaviour |
|---|---|
| Validation or rule failure | 400 `{"detail": ...}` |
| Missing record | 404 |
| Illegal state change | 400 with both states named |
| Upstream (inventory) unavailable during PO creation | 503 |
| Gateway cannot reach a service | 502; timeout 504 |
| Redis / RabbitMQ failure | Logged, request continues |
