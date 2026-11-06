"""Seed sample suppliers in procurement_db."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from faker import Faker
from app.core.database import SessionLocal
from app.modules.suppliers.models import Supplier
fake=Faker()
db=SessionLocal()
try:
    if db.query(Supplier).count() == 0:
        suppliers=[Supplier(code=f"SUP-{i+1:04d}",name=fake.company(),contact_person=fake.name(),email=fake.company_email(),phone=fake.phone_number()[:15],address=fake.address(),lead_time_days=fake.random_int(min=3,max=21),is_active=True) for i in range(6)]
        db.add_all(suppliers); db.commit(); print(f"Procurement seed complete: {len(suppliers)} suppliers")
    else: print("Procurement already contains suppliers; seed skipped")
except Exception:
    db.rollback(); raise
finally: db.close()
