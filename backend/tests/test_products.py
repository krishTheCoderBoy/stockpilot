from app.modules.users.models import UserRole


def test_create_and_get_product(client, auth_headers):
    headers, _ = auth_headers(UserRole.INVENTORY_MANAGER)
    res = client.post(
        "/products/",
        headers=headers,
        json={"sku": "SKU-TEST-1", "name": "Test Widget", "unit_price": 10.5},
    )
    assert res.status_code == 201
    product_id = res.json()["id"]

    res = client.get(f"/products/{product_id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["sku"] == "SKU-TEST-1"


def test_duplicate_sku_rejected(client, auth_headers):
    headers, _ = auth_headers(UserRole.INVENTORY_MANAGER)
    payload = {"sku": "SKU-DUP", "name": "Widget A", "unit_price": 5}
    client.post("/products/", headers=headers, json=payload)
    res = client.post("/products/", headers=headers, json={**payload, "name": "Widget B"})
    assert res.status_code == 400


def test_procurement_manager_can_read_but_not_write_products(client, auth_headers):
    headers, _ = auth_headers(UserRole.PROCUREMENT_MANAGER)
    res = client.get("/products/", headers=headers)
    assert res.status_code == 200

    res = client.post("/products/", headers=headers, json={"sku": "X", "name": "X", "unit_price": 1})
    assert res.status_code == 403