import uuid

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings
from app.core.security import hash_password
from app.modules.users.models import User, UserRole
from app.core.limiter import limiter

test_engine = create_engine(settings.test_database_url)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def db_session():
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)

    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(sess, trans):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def make_user(db_session):
    def _make_user(email: str, role: UserRole, password: str = "Test@1234"):
        user = User(
            username=email.split("@")[0],
            email=email,
            mobile_no=f"9{uuid.uuid4().int % 10**9:09d}",
            hashed_password=hash_password(password),
            full_name="Test User",
            role=role,
            is_active=True,
            is_verified=True,
            otp_verified_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user, password

    return _make_user


@pytest.fixture()
def auth_headers(client, make_user):
    def _auth_headers(role: UserRole, email: str = None):
        email = email or f"{role.value.lower()}-{uuid.uuid4().hex[:6]}@test.com"
        user, password = make_user(email, role)
        res = client.post("/auth/login", json={"email": email, "password": password})
        token = res.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}, user

    return _auth_headers

@pytest.fixture(autouse=True)
def reset_rate_limiter():
    limiter.reset()
    yield