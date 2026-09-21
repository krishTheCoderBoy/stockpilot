import random
import sys
from pathlib import Path
from decimal import Decimal

sys.path.append(str(Path(__file__).resolve().parents[1]))

from faker import Faker

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.modules.users.models import User, UserRole
from app.modules.products.categories_models import ProductCategory
from app.modules.products.models import Product
from app.modules.warehouses.models import Warehouse, WarehouseType
from app.modules.suppliers.models import Supplier
from app.modules.inventory_movements.service import MovementService
from app.modules.inventory_movements.models import MovementType
from app.modules.inventory_movements.models import ReferenceType

fake = Faker()
db = SessionLocal()

print("Seeding StockPilot database...")

# --- Admin user (known credentials, solves lost-password problem) ---
ADMIN_EMAIL = "admin@stockpilot.com"
ADMIN_PASSWORD = "Admin@1234"

existing_admin = db.query(User).filter(User.email == ADMIN_EMAIL).first()
if not existing_admin:
    admin = User(
        username="admin",
        email=ADMIN_EMAIL,
        mobile_no="9000000000",
        address="Kolkata, India",
        hashed_password=hash_password(ADMIN_PASSWORD),
        full_name="System Admin",
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    print(f"Created admin: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
else:
    admin = existing_admin
    print(f"Admin already exists: {ADMIN_EMAIL}")

# --- Inventory + Procurement managers ---
managers = []
for role in [UserRole.INVENTORY_MANAGER, UserRole.PROCUREMENT_MANAGER]:
    for _ in range(2):
        email = fake.unique.email()
        user = User(
            username=fake.unique.user_name(),
            email=email,
            mobile_no=fake.unique.msisdn()[:10],
            address=fake.address(),
            hashed_password=hash_password("Test@1234"),
            full_name=fake.name(),
            role=role,
            is_active=True,
            is_verified=True,
        )
        db.add(user)
        managers.append(user)
db.commit()
print(f"Created {len(managers)} manager users (password: Test@1234)")

# --- Product categories ---
category_names = ["Electronics", "Packaging", "Raw Materials", "Office Supplies", "Hardware"]
categories = []
for name in category_names:
    cat = ProductCategory(name=name)
    db.add(cat)
    categories.append(cat)
db.commit()
print(f"Created {len(categories)} categories")

# --- Suppliers ---
suppliers = []
for _ in range(6):
    supplier = Supplier(
        code=f"SUP-{fake.unique.random_number(digits=4)}",
        name=fake.company(),
        contact_person=fake.name(),
        email=fake.company_email(),
        phone=fake.phone_number()[:15],
        address=fake.address(),
        lead_time_days=random.randint(3, 21),
    )
    db.add(supplier)
    suppliers.append(supplier)
db.commit()
print(f"Created {len(suppliers)} suppliers")

# --- Warehouses ---
warehouse_data = [
    ("WH-KOL-01", "Kolkata Main", "Kolkata", "West Bengal", WarehouseType.MAIN),
    ("WH-DEL-01", "Delhi Regional", "Delhi", "Delhi", WarehouseType.REGIONAL),
    ("WH-BLR-01", "Bangalore Regional", "Bangalore", "Karnataka", WarehouseType.REGIONAL),
    ("WH-MUM-01", "Mumbai Transit", "Mumbai", "Maharashtra", WarehouseType.TRANSIT),
]
warehouses = []
for code, name, city, state, wtype in warehouse_data:
    wh = Warehouse(
        code=code,
        name=name,
        city=city,
        state=state,
        country="India",
        manager_id=random.choice(managers).id,
        capacity=Decimal(random.randint(5000, 20000)),
        warehouse_type=wtype,
    )
    db.add(wh)
    warehouses.append(wh)
db.commit()
print(f"Created {len(warehouses)} warehouses")

# --- Products ---
products = []
for _ in range(30):
    unit_price = Decimal(str(round(random.uniform(50, 5000), 2)))
    product = Product(
        sku=f"SKU-{fake.unique.random_number(digits=5)}",
        name=fake.unique.catch_phrase(),
        description=fake.sentence(),
        category_id=random.choice(categories).id,
        unit_price=unit_price,
        unit_of_measure=random.choice(["unit", "box", "kg", "pack"]),
        reorder_point=Decimal(random.randint(10, 50)),
        min_order_quantity=Decimal(random.randint(1, 10)),
        max_stock_level=Decimal(random.randint(500, 2000)),
        default_supplier_id=random.choice(suppliers).id,
    )
    db.add(product)
    products.append(product)
db.commit()
print(f"Created {len(products)} products")

# --- Inventory movements (RECEIVE stock into warehouses) ---
movement_service = MovementService(db)
movement_count = 0
for product in products:
    for warehouse in random.sample(warehouses, k=random.randint(1, 3)):
        qty = Decimal(random.randint(50, 300))
        cost = product.unit_price * Decimal("0.7")
        movement_service._apply_single_movement(
            product_id=product.id,
            warehouse_id=warehouse.id,
            movement_type=MovementType.RECEIVE,
            quantity=qty,
            unit_cost=cost,
            reference_type=ReferenceType.MANUAL,
            reference_id=None,
            performed_by=admin.id,
            notes="Initial seed stock",
        )
        movement_count += 1
db.commit()
print(f"Created {movement_count} initial RECEIVE movements")

# --- A few ISSUE movements for realistic movement history ---
issue_count = 0
for product in random.sample(products, k=15):
    for warehouse in random.sample(warehouses, k=1):
        try:
            movement_service._apply_single_movement(
                product_id=product.id,
                warehouse_id=warehouse.id,
                movement_type=MovementType.ISSUE,
                quantity=Decimal(random.randint(5, 30)),
                unit_cost=None,
                reference_type=ReferenceType.MANUAL,
                reference_id=None,
                performed_by=random.choice(managers).id,
                notes="Simulated outbound usage",
            )
            issue_count += 1
        except Exception:
            db.rollback()
            continue
db.commit()
print(f"Created {issue_count} ISSUE movements")

db.close()
print("Seeding complete.")