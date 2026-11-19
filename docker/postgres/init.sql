-- One database per service (see docs/database.md). The official image runs this only on
-- the first start of an empty data volume; use `docker compose down -v` to re-run it.
-- Tables are created by each service's `alembic upgrade head`, not here.
CREATE DATABASE auth_db;
CREATE DATABASE inventory_db;
CREATE DATABASE procurement_db;
