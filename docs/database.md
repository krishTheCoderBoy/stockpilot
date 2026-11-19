# Database

Each service owns one PostgreSQL database and is the only code that touches it. Schema changes go through that service's Alembic migrations (`services/<service>/alembic/versions`). No service reads another service's tables.

| Service | Database | Tables |
|---|---|---|
| auth-service | `auth_db` | `users`, `otps` |
| inventory-service | `inventory_db` | `product_categories`, `products`, `warehouses`, `inventory`, `inventory_movements`, `inventory_batches`, `stock_reservations` |
| procurement-service | `procurement_db` | `suppliers`, `purchase_orders`, `purchase_order_items` |

All primary keys are UUIDs. Quantities are `NUMERIC(14,2)`, money is `NUMERIC(12,2)`; floats are never used.

## auth_db

- **users**: `username`, `email`, `mobile_no` (all unique), `hashed_password`, `full_name`, `role` (`user_role`: `ADMIN`, `INVENTORY_MANAGER`, `PROCUREMENT_MANAGER`), `is_active`, `is_verified`, `otp_verified_at`.
- **otps**: one-time codes. `user_id` → `users.id` (a real foreign key, same database), `code` (6 chars), `purpose` (`REGISTRATION`, `LOGIN`, `PASSWORD_RESET`), `is_used`, `expires_at`.

## inventory_db

- **product_categories**: `name` (unique), `parent_category_id` → itself.
- **products**: `sku` (unique), `name`, `description`, `category_id`, `unit_price`, `unit_of_measure`, `reorder_point`, `min_order_quantity`, `max_stock_level`, `is_active`, `default_supplier_id`, `search_vector`.
- **warehouses**: `code` (unique), `name`, `city`, `state`, `country`, `warehouse_type` (`MAIN`, `REGIONAL`, `TRANSIT`), `capacity`, `manager_id`, `is_active`, `search_vector`.
- **inventory**: one row per (product, warehouse), unique on that pair. `on_hand_quantity`, `reserved_quantity`, `average_unit_cost`, `safety_stock_override`, `last_movement_at`. Available stock is `on_hand − reserved`, defined once as `Inventory.available_quantity`. Constraints: `reserved_quantity >= 0` and `reserved_quantity <= on_hand_quantity`.
- **inventory_movements**: append-only ledger, never updated or deleted. `movement_type` is one of `RECEIVE`, `ISSUE`, `ADJUSTMENT_INCREASE`, `ADJUSTMENT_DECREASE`, `TRANSFER_IN`, `TRANSFER_OUT`, `DAMAGED`, `RETURNED`. `reference_type` is `MANUAL`, `PURCHASE_ORDER` or `TRANSFER`. Indexes `(product_id, movement_type, created_at)` and `(movement_type, created_at)` serve the demand-history query (ISSUE rows in a date range, for one product or all).
- **inventory_batches**: created by `RECEIVE`. `batch_number`, `received_quantity`, `remaining_quantity`, `expiry_date`, `movement_id` → `inventory_movements.id`. `ISSUE` and `DAMAGED` consume batches soonest-expiry first.
- **stock_reservations**: explicit holds. `quantity` (> 0), `status` (`ACTIVE`, `RELEASED`, `FULFILLED`), free-form `reference_type` / `reference_id`, `fulfilled_quantity`, `fulfillment_movement_id` → `inventory_movements.id`. `inventory.reserved_quantity` equals the sum of `ACTIVE` reservations for that row.

### Movement direction

| Stock in | Stock out |
|---|---|
| `RECEIVE`, `ADJUSTMENT_INCREASE`, `TRANSFER_IN`, `RETURNED` | `ISSUE`, `ADJUSTMENT_DECREASE`, `TRANSFER_OUT`, `DAMAGED` |

`ISSUE` is real demand. `DAMAGED` (write-off) and `RETURNED` are kept as separate types so demand forecasting can exclude them.

## procurement_db

- **suppliers**: `code` (unique), `name`, `contact_person`, `email`, `phone`, `address`, `lead_time_days`, `is_active`.
- **purchase_orders**: `po_number` (unique), `supplier_id` → `suppliers.id`, `warehouse_id`, `status` (`po_status`), `created_by`, `approved_by`, `notes`, `expected_date`, timestamps.
- **purchase_order_items**: `purchase_order_id` → `purchase_orders.id`, `product_id`, `ordered_quantity`, `received_quantity`, `unit_price`.

`po_status`: `DRAFT`, `SUBMITTED`, `APPROVED`, `ORDERED`, `PARTIALLY_RECEIVED`, `RECEIVED`, `CLOSED`, `CANCELLED`.

## Cross-service references (UUIDs without foreign keys)

The owning row lives in another database, so these columns are plain UUIDs. They are validated through the owning service's API when written, or trusted from the verified JWT or an event payload.

| Column | Points at | Checked by |
|---|---|---|
| `inventory.products.default_supplier_id` | procurement `suppliers.id` | not enforced |
| `inventory.warehouses.manager_id` | auth `users.id` | not enforced |
| `inventory.inventory_movements.performed_by` | auth `users.id` | JWT `sub` |
| `inventory.stock_reservations.created_by` | auth `users.id` | JWT `sub` |
| `procurement.purchase_orders.warehouse_id` | inventory `warehouses.id` | HTTP call at PO creation |
| `procurement.purchase_orders.created_by` / `approved_by` | auth `users.id` | JWT `sub` |
| `procurement.purchase_order_items.product_id` | inventory `products.id` | HTTP call at PO creation |

Consequence: deleting or deactivating a product, warehouse or user in its owning service does not cascade. Nothing deletes those rows today (they are deactivated), so references stay resolvable.

## Search columns

`products.search_vector`, `warehouses.search_vector`, `suppliers.search_vector` and `purchase_orders.search_vector` are PostgreSQL generated `tsvector` columns with GIN indexes. The application never writes them. `inventory_movements.search_vector` is the fifth. All five are declared in their model with `Computed` and created by idempotent migrations. The movements vector covers only `notes` (a generated column cannot read other tables, and the enum reference type is not immutable); movement search additionally matches movements whose product or warehouse matches, using those tables' own vectors.

## Migrations

- Each service has its own revision chain. Revision `0001` is explicit DDL, frozen at the service split. It must not call `Base.metadata.create_all()`, which makes the baseline follow the live models and breaks later migrations. Inventory's is frozen; auth-service's `0001` still calls `create_all()` and must be frozen before its first later migration.
- Enum values are added with `ALTER TYPE ... ADD VALUE IF NOT EXISTS` inside `autocommit_block()`. PostgreSQL cannot drop enum values, so those downgrades leave the value in place.
- Moving data from the old shared database: `services/<service>/scripts/migrate_data.py` (see [database-per-service.md](database-per-service.md)).
