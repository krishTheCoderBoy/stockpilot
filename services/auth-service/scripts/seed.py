"""Seed an administrator and sample managers in auth_db."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.modules.users.models import User, UserRole
db=SessionLocal()
try:
    existing={u.email for u in db.query(User).all()}
    if "admin@stockpilot.com" not in existing:
        db.add(User(username="admin",email="admin@stockpilot.com",mobile_no="9000000000",address="Kolkata, India",hashed_password=hash_password("Admin@1234"),full_name="System Admin",role=UserRole.ADMIN,is_active=True,is_verified=True))
    for role in (UserRole.INVENTORY_MANAGER,UserRole.PROCUREMENT_MANAGER):
        if not any(u.role == role for u in db.query(User).all()):
            suffix=role.value.lower()
            db.add(User(username=suffix,email=f"{suffix}@stockpilot.com",mobile_no=None,hashed_password=hash_password("Test@1234"),full_name=role.value.replace("_"," ").title(),role=role,is_active=True,is_verified=True))
    db.commit()
    print("Auth seed complete. Admin: admin@stockpilot.com / Admin@1234")
except Exception:
    db.rollback(); raise
finally: db.close()
