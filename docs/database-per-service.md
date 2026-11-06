# Database separation (Milestone 46)

Each service now reads its own `DATABASE_URL`: `auth_db`, `inventory_db`, and `procurement_db`. Copy each service's `.env.example` to `.env` and set its target connection and the shared JWT secret before starting services. `DATABASE_URL` defaults and the local `.env` values point to the respective database names.

To migrate the existing shared database, run each one-time copier from its service directory after configuring that service's destination `DATABASE_URL`:

```powershell
python scripts/migrate_data.py --source-url 'postgresql+psycopg2://USER:PASSWORD@HOST:5432/stockpilot_db'
```

The copier creates the destination database if needed (the database account needs `CREATEDB`), runs that service's Alembic schema baseline, and copies only the tables it owns. It refuses to copy into the shared source DB or into populated target tables. Run it once per service. Keep the old shared database until all three copies are verified through the applications.

For a fresh setup, first run `alembic upgrade head` from each service directory after creating/configuring its target database. Seed the databases separately with `python scripts/seed.py` from each service directory. `backend/scripts/seed.py` remains as a dispatcher for all three service seeders.

Cross-service identifiers remain UUID columns without database foreign keys: inventory's `products.default_supplier_id`, `warehouses.manager_id`, and `inventory_movements.performed_by`; procurement's PO `warehouse_id`, `created_by`, `approved_by`, and PO item `product_id`. These values are validated through service APIs or trusted from authenticated/event payloads because the owning rows live in another database. Inventory relationships among products, categories, warehouses, movements, stock, and batches remain enforced. Procurement keeps its local PO-to-supplier and PO-to-item foreign keys.
