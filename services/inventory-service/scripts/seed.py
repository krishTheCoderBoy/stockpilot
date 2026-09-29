"""Seed inventory catalog, warehouses, and starting stock in inventory_db."""
import random
import sys
from decimal import Decimal
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.core.database import SessionLocal
from app.modules.products.categories_models import ProductCategory
from app.modules.products.models import Product
from app.modules.warehouses.models import Warehouse, WarehouseType
from app.modules.inventory_movements.models import MovementType, ReferenceType
from app.modules.inventory_movements.service import MovementService
db=SessionLocal()
try:
    if db.query(Product).count() == 0:
        categories=[ProductCategory(name=n) for n in ("Electronics","Packaging","Raw Materials","Office Supplies","Hardware")]
        db.add_all(categories); db.flush()
        warehouse_specs=[("WH-KOL-01","Kolkata Main","Kolkata","West Bengal",WarehouseType.MAIN),("WH-DEL-01","Delhi Regional","Delhi","Delhi",WarehouseType.REGIONAL),("WH-BLR-01","Bangalore Regional","Bangalore","Karnataka",WarehouseType.REGIONAL),("WH-MUM-01","Mumbai Transit","Mumbai","Maharashtra",WarehouseType.TRANSIT)]
        warehouses=[Warehouse(code=c,name=n,city=city,state=state,country="India",capacity=Decimal("10000"),warehouse_type=typ,manager_id=None) for c,n,city,state,typ in warehouse_specs]
        db.add_all(warehouses); db.flush()
        products=[]
        for i in range(30):
            products.append(Product(sku=f"SKU-{i+1:05d}",name=f"Sample product {i+1}",description="Seeded inventory item",category_id=random.choice(categories).id,unit_price=Decimal(str(random.randint(50,5000))),unit_of_measure=random.choice(["unit","box","kg","pack"]),reorder_point=Decimal("20"),min_order_quantity=Decimal("1"),max_stock_level=Decimal("1000"),default_supplier_id=None))
        db.add_all(products); db.flush()
        movement_service=MovementService(db)
        for product in products:
            for warehouse in random.sample(warehouses,k=random.randint(1,3)):
                movement_service._apply_single_movement(product_id=product.id,warehouse_id=warehouse.id,movement_type=MovementType.RECEIVE,quantity=Decimal(random.randint(50,300)),unit_cost=product.unit_price*Decimal("0.7"),reference_type=ReferenceType.MANUAL,reference_id=None,performed_by=None,notes="Initial seed stock")
        db.commit()
        print(f"Inventory seed complete: {len(products)} products and {len(warehouses)} warehouses")
    else: print("Inventory already contains products; seed skipped")
except Exception:
    db.rollback(); raise
finally: db.close()
