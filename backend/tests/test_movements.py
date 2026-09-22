from app.modules.users.models import UserRole


def _create_product_and_warehouse(client, headers):
    p = client.post("/products/", headers=headers, json={"sku": "SKU-MV1", "name": "Widget", "unit_price": 10}).json()
    w = client.post(
        "/warehouses/",
        headers={**headers},
        json={"code": "WH-MV1", "name": "Test WH", "city": "X", "state": "Y", "country": "Z"},
    )
    return p, w


def test_receive_and_issue_updates_inventory(client, auth_headers):
    admin_headers, _ = auth_headers(UserRole.ADMIN)
    inv_headers, _ = auth_headers(UserRole.INVENTORY_MANAGER, email="im@test.com")

    product = client.post("/products/", headers=inv_headers, json={"sku": "SKU-MV2", "name": "Widget", "unit_price": 10}).json()
    warehouse = client.post(
        "/warehouses/", headers=admin_headers,
        json={"code": "WH-MV2", "name": "Test WH", "city": "X", "state": "Y", "country": "Z"},
    ).json()

    res = client.post(
        "/inventory-movements/", headers=inv_headers,
        json={"product_id": product["id"], "warehouse_id": warehouse["id"], "movement_type": "RECEIVE", "quantity": 100, "unit_cost": 5},
    )
    assert res.status_code == 201

    inv = client.get(f"/inventory/{product['id']}/{warehouse['id']}", headers=inv_headers).json()
    assert float(inv["on_hand_quantity"]) == 100

    res = client.post(
        "/inventory-movements/", headers=inv_headers,
        json={"product_id": product["id"], "warehouse_id": warehouse["id"], "movement_type": "ISSUE", "quantity": 30},
    )
    assert res.status_code == 201

    inv = client.get(f"/inventory/{product['id']}/{warehouse['id']}", headers=inv_headers).json()
    assert float(inv["on_hand_quantity"]) == 70


def test_issue_more_than_available_rejected(client, auth_headers):
    headers, _ = auth_headers(UserRole.INVENTORY_MANAGER, email="im2@test.com")
    admin_headers, _ = auth_headers(UserRole.ADMIN, email="admin2@test.com")

    product = client.post("/products/", headers=headers, json={"sku": "SKU-MV3", "name": "Widget", "unit_price": 10}).json()
    warehouse = client.post(
        "/warehouses/", headers=admin_headers,
        json={"code": "WH-MV3", "name": "Test WH", "city": "X", "state": "Y", "country": "Z"},
    ).json()

    client.post(
        "/inventory-movements/", headers=headers,
        json={"product_id": product["id"], "warehouse_id": warehouse["id"], "movement_type": "RECEIVE", "quantity": 10, "unit_cost": 5},
    )

    res = client.post(
        "/inventory-movements/", headers=headers,
        json={"product_id": product["id"], "warehouse_id": warehouse["id"], "movement_type": "ISSUE", "quantity": 999},
    )
    assert res.status_code == 400

    inv = client.get(f"/inventory/{product['id']}/{warehouse['id']}", headers=headers).json()
    assert float(inv["on_hand_quantity"]) == 10  # unchanged — confirms rollback worked