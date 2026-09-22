from app.modules.users.models import UserRole


def test_login_success(client, auth_headers):
    headers, user = auth_headers(UserRole.ADMIN)
    res = client.get("/users/me", headers=headers)
    assert res.status_code == 200
    assert res.json()["email"] == user.email


def test_login_wrong_password(client, make_user):
    make_user("wrongpass@test.com", UserRole.ADMIN)
    res = client.post("/auth/login", json={"email": "wrongpass@test.com", "password": "bad"})
    assert res.status_code == 401


def test_unverified_user_cannot_login(client, db_session):
    from app.core.security import hash_password
    from app.modules.users.models import User

    user = User(
        username="unverified",
        email="unverified@test.com",
        mobile_no="9111111111",
        hashed_password=hash_password("Test@1234"),
        full_name="Unverified User",
        role=UserRole.INVENTORY_MANAGER,
        is_active=True,
        is_verified=False,
    )
    db_session.add(user)
    db_session.commit()

    res = client.post("/auth/login", json={"email": "unverified@test.com", "password": "Test@1234"})
    assert res.status_code == 403


def test_rbac_blocks_non_admin_from_creating_user(client, auth_headers):
    headers, _ = auth_headers(UserRole.INVENTORY_MANAGER)
    res = client.post(
        "/users/",
        headers=headers,
        json={
            "username": "newguy", "email": "newguy@test.com", "mobile_no": "9222222222",
            "password": "Test@1234", "full_name": "New Guy", "role": "INVENTORY_MANAGER",
        },
    )
    assert res.status_code == 403