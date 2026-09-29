"""Copy this service's tables from the former shared database into its own database."""
import sys
from pathlib import Path
service_root = Path(__file__).resolve().parents[1]
services_root = service_root.parent
sys.path.insert(0, str(services_root))
from shared.migrations.copy_data import copy_owned_tables
if __name__ == "__main__":
    copy_owned_tables(service_root, ['suppliers', 'purchase_orders', 'purchase_order_items'])
