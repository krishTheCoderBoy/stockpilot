"""One-time PostgreSQL table copier for isolated StockPilot services."""
import argparse
import os
from pathlib import Path
from sqlalchemy import MetaData, create_engine, insert, inspect, select, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.pool import NullPool
def _create_database_if_missing(target: URL) -> None:
    if target.get_backend_name() != "postgresql":
        raise ValueError("Service data migration currently supports PostgreSQL only")
    database = target.database
    if not database or database == "postgres":
        raise ValueError("DATABASE_URL must name a dedicated service database")
    admin = target.set(database="postgres")
    engine = create_engine(admin, isolation_level="AUTOCOMMIT", poolclass=NullPool)
    try:
        with engine.connect() as connection:
            exists = connection.execute(text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": database}).scalar()
            if not exists:
                identifier = connection.dialect.identifier_preparer.quote(database)
                connection.exec_driver_sql(f"CREATE DATABASE {identifier}")
    finally:
        engine.dispose()
def copy_owned_tables(service_root: Path, table_names: list[str]) -> None:
    parser = argparse.ArgumentParser(description="Copy only this service's owned tables from the shared database.")
    parser.add_argument("--source-url", required=True, help="Existing shared PostgreSQL DATABASE_URL")
    args = parser.parse_args()
    os.chdir(service_root)
    from app.core.config import settings
    target_url = make_url(settings.database_url)
    source_url = make_url(args.source_url)
    if target_url.get_backend_name() != source_url.get_backend_name() or (target_url.host, target_url.port, target_url.database) == (source_url.host, source_url.port, source_url.database):
        raise ValueError("Source and target must be distinct databases on the same database backend")
    _create_database_if_missing(target_url)
    from alembic import command
    from alembic.config import Config
    config = Config(str(service_root / "alembic.ini"))
    config.set_main_option("script_location", str(service_root / "alembic").replace("%", "%%"))
    command.upgrade(config, "head")
    source_engine = create_engine(source_url, pool_pre_ping=True, poolclass=NullPool)
    target_engine = create_engine(target_url, pool_pre_ping=True, poolclass=NullPool)
    try:
        source_metadata = MetaData()
        source_metadata.reflect(bind=source_engine, only=table_names)
        missing = set(table_names) - set(source_metadata.tables)
        if missing:
            raise RuntimeError(f"Source database is missing owned tables: {', '.join(sorted(missing))}")
        with target_engine.begin() as target_connection, source_engine.connect() as source_connection:
            target_names = set(inspect(target_connection).get_table_names())
            target_metadata = MetaData()
            target_metadata.reflect(bind=target_connection, only=table_names)
            for name in table_names:
                if name not in target_names:
                    raise RuntimeError(f"Target migration did not create table {name}")
                destination = target_metadata.tables[name]
                if target_connection.execute(select(destination).limit(1)).first():
                    raise RuntimeError(f"Target table {name} already contains rows; refusing a duplicate migration")
            for name in table_names:
                source_table = source_metadata.tables[name]
                destination = target_metadata.tables[name]
                source_columns = {column.name for column in source_table.columns}
                target_columns = {column.name for column in destination.columns}
                if source_columns != target_columns:
                    raise RuntimeError(f"Source and target columns differ for {name}")
                result = source_connection.execution_options(stream_results=True).execute(select(source_table))
                while rows := result.fetchmany(1000):
                    batch = [dict(row._mapping) for row in rows]
                    target_connection.execute(insert(destination), batch)
                result.close()
    finally:
        source_engine.dispose()
        target_engine.dispose()
