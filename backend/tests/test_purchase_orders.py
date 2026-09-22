from app.modules.users.models import UserRole


def _setup(client, procurement_headers, admin_headers):
    supplier = client.post(
        "/suppliers/", headers=procurement_headers,
        json={"code": "SUP-T1", "name": "Test Supplier"},
    ).json()
    warehouse = client.post(
        "/warehouses/", headers=admin_headers,
        json={"code": "WH-PO1", "name": "Test WH", "city": "X", "state": "Y", "country": "Z"},
    ).json()
    product = client.post(
        "/products/", headers=procurement_headers,
        json={"sku": "SKU-PO1", "name": "Widget", "unit_price": 10},
    )
    if product.status_code != 201:
        product = client.post(
            "/products/", headers=admin_headers,
            json={"sku": "SKU-PO1", "name": "Widget", "unit_price": 10},
        )
    product = product.json()
    return supplier, warehouse, product


def test_full_po_lifecycle(client, auth_headers):
    admin_headers, _ = auth_headers(UserRole.ADMIN)
    proc_headers, _ = auth_headers(UserRole.PROCUREMENT_MANAGER)

    supplier, warehouse, product = _setup(client, proc_headers, admin_headers)

    res = client.post(
        "/purchase-orders/", headers=proc_headers,
        json={
            "supplier_id": supplier["id"], "warehouse_id": warehouse["id"],
            "items": [{"product_id": product["id"], "ordered_quantity": 100, "unit_price": 10}],
        },
    )
    assert res.status_code == 201
    po = res.json()
    assert po["status"] == "DRAFT"

    res = client.post(f"/purchase-orders/{po['id']}/submit", headers=proc_headers)
    assert res.json()["status"] == "SUBMITTED"

    res = client.post(f"/purchase-orders/{po['id']}/mark-ordered", headers=proc_headers)
    assert res.status_code == 400  # can't skip approval

    res = client.post(f"/purchase-orders/{po['id']}/approve", headers=admin_headers)
    assert res.json()["status"] == "APPROVED"

    res = client.post(f"/purchase-orders/{po['id']}/mark-ordered", headers=proc_headers)
    assert res.json()["status"] == "ORDERED"

    item_id = po["items"][0]["id"]
    res = client.post(
        f"/purchase-orders/{po['id']}/receive", headers=proc_headers,
        json={"items": [{"po_item_id": item_id, "quantity": 40}]},
    )
    assert res.json()["status"] == "PARTIALLY_RECEIVED"

    res = client.post(
        f"/purchase-orders/{po['id']}/receive", headers=proc_headers,
        json={"items": [{"po_item_id": item_id, "quantity": 60}]},
    )
    assert res.json()["status"] == "RECEIVED"

    inv = client.get(f"/inventory/{product['id']}/{warehouse['id']}", headers=proc_headers).json()
    assert float(inv["on_hand_quantity"]) == 100

    res = client.post(f"/purchase-orders/{po['id']}/close", headers=proc_headers)
    assert res.json()["status"] == "CLOSED"


def test_over_receiving_rejected(client, auth_headers):
    admin_headers, _ = auth_headers(UserRole.ADMIN, email="admin3@test.com")
    proc_headers, _ = auth_headers(UserRole.PROCUREMENT_MANAGER, email="proc3@test.com")

    supplier, warehouse, product = _setup(client, proc_headers, admin_headers)

    po = client.post(
        "/purchase-orders/", headers=proc_headers,
        json={
            "supplier_id": supplier["id"], "warehouse_id": warehouse["id"],
            "items": [{"product_id": product["id"], "ordered_quantity": 50, "unit_price": 10}],
        },
    ).json()
    client.post(f"/purchase-orders/{po['id']}/submit", headers=proc_headers)
    client.post(f"/purchase-orders/{po['id']}/approve", headers=admin_headers)
    client.post(f"/purchase-orders/{po['id']}/mark-ordered", headers=proc_headers)

    item_id = po["items"][0]["id"]
    res = client.post(
        f"/purchase-orders/{po['id']}/receive", headers=proc_headers,
        json={"items": [{"po_item_id": item_id, "quantity": 999}]},
    )
    assert res.status_code == 400