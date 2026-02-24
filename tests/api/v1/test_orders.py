import pytest
from httpx import AsyncClient


# ── Fixtures / helpers ────────────────────────────────────────────────────────

async def _create_supplier(client: AsyncClient, name: str) -> dict:
    resp = await client.post("/api/v1/suppliers", json={"name": name})
    assert resp.status_code == 201
    return resp.json()


async def _create_product(client: AsyncClient, name: str, sku: str) -> dict:
    resp = await client.post("/api/v1/products", json={"name": name, "sku": sku, "unit": "pcs"})
    assert resp.status_code == 201
    return resp.json()


async def _link_product(
    client: AsyncClient,
    supplier_id: str,
    product_id: str,
    min_qty: float = 5.0,
    optimal_qty: float = 20.0,
    unit_price: str | None = "10.00",
) -> dict:
    payload: dict = {
        "product_id": product_id,
        "minimum_quantity": min_qty,
        "optimal_quantity": optimal_qty,
    }
    if unit_price is not None:
        payload["unit_price"] = unit_price
    resp = await client.post(f"/api/v1/suppliers/{supplier_id}/products", json=payload)
    assert resp.status_code == 201
    return resp.json()


async def _create_order(client: AsyncClient, supplier_id: str, notes: str | None = None) -> dict:
    payload: dict = {"supplier_id": supplier_id}
    if notes:
        payload["notes"] = notes
    resp = await client.post("/api/v1/orders", json=payload)
    assert resp.status_code == 201
    return resp.json()


# ── Order CRUD ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_order(client: AsyncClient) -> None:
    supplier = await _create_supplier(client, "Order Supplier 1")
    response = await client.post(
        "/api/v1/orders", json={"supplier_id": supplier["id"], "notes": "First order"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "DRAFT"
    assert data["total"] == "0.0000"
    assert data["supplier"]["id"] == supplier["id"]


@pytest.mark.asyncio
async def test_create_order_invalid_supplier(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/orders",
        json={"supplier_id": "00000000-0000-0000-0000-000000000000"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_orders(client: AsyncClient) -> None:
    supplier = await _create_supplier(client, "List Orders Supplier")
    await _create_order(client, supplier["id"])
    await _create_order(client, supplier["id"])
    response = await client.get("/api/v1/orders")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_list_orders_filter_by_supplier(client: AsyncClient) -> None:
    s1 = await _create_supplier(client, "Filter Supplier A")
    s2 = await _create_supplier(client, "Filter Supplier B")
    await _create_order(client, s1["id"])
    await _create_order(client, s2["id"])
    response = await client.get(f"/api/v1/orders?supplier_id={s1['id']}")
    assert response.status_code == 200
    orders = response.json()
    assert all(o["supplier_id"] == s1["id"] for o in orders)


@pytest.mark.asyncio
async def test_get_order_with_items(client: AsyncClient) -> None:
    supplier = await _create_supplier(client, "Get Order Supplier")
    order = await _create_order(client, supplier["id"])
    response = await client.get(f"/api/v1/orders/{order['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == order["id"]
    assert data["items"] == []


@pytest.mark.asyncio
async def test_get_order_not_found(client: AsyncClient) -> None:
    response = await client.get("/api/v1/orders/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_order_notes(client: AsyncClient) -> None:
    supplier = await _create_supplier(client, "Update Notes Supplier")
    order = await _create_order(client, supplier["id"])
    response = await client.patch(
        f"/api/v1/orders/{order['id']}", json={"notes": "Updated notes"}
    )
    assert response.status_code == 200
    assert response.json()["notes"] == "Updated notes"


@pytest.mark.asyncio
async def test_delete_draft_order(client: AsyncClient) -> None:
    supplier = await _create_supplier(client, "Delete Draft Supplier")
    order = await _create_order(client, supplier["id"])
    response = await client.delete(f"/api/v1/orders/{order['id']}")
    assert response.status_code == 204
    get_response = await client.get(f"/api/v1/orders/{order['id']}")
    assert get_response.status_code == 404


# ── Status transitions ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_confirm_order(client: AsyncClient) -> None:
    supplier = await _create_supplier(client, "Confirm Supplier")
    order = await _create_order(client, supplier["id"])
    response = await client.patch(
        f"/api/v1/orders/{order['id']}/status", json={"status": "CONFIRMED"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "CONFIRMED"


@pytest.mark.asyncio
async def test_invalid_status_transition(client: AsyncClient) -> None:
    supplier = await _create_supplier(client, "Invalid Trans Supplier")
    order = await _create_order(client, supplier["id"])
    # DRAFT → SENT is not allowed
    response = await client.patch(
        f"/api/v1/orders/{order['id']}/status", json={"status": "SENT"}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_delete_confirmed_order_fails(client: AsyncClient) -> None:
    supplier = await _create_supplier(client, "No Delete Confirmed Supplier")
    order = await _create_order(client, supplier["id"])
    await client.patch(f"/api/v1/orders/{order['id']}/status", json={"status": "CONFIRMED"})
    response = await client.delete(f"/api/v1/orders/{order['id']}")
    assert response.status_code == 422


# ── Order items ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_add_item_to_order(client: AsyncClient) -> None:
    supplier = await _create_supplier(client, "Item Supplier 1")
    product = await _create_product(client, "Bolt A", "BOLT-A")
    await _link_product(client, supplier["id"], product["id"], min_qty=5.0, unit_price="2.50")
    order = await _create_order(client, supplier["id"])

    response = await client.post(
        f"/api/v1/orders/{order['id']}/items",
        json={"product_id": product["id"], "quantity": 10.0},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["quantity"] == 10.0
    assert data["subtotal"] == "25.0000"   # 10 × 2.50
    assert data["unit_price"] is None      # DRAFT: not snapshotted yet


@pytest.mark.asyncio
async def test_add_item_updates_order_total(client: AsyncClient) -> None:
    supplier = await _create_supplier(client, "Total Supplier")
    product = await _create_product(client, "Gear B", "GEAR-B")
    await _link_product(client, supplier["id"], product["id"], min_qty=1.0, unit_price="5.00")
    order = await _create_order(client, supplier["id"])
    await client.post(
        f"/api/v1/orders/{order['id']}/items",
        json={"product_id": product["id"], "quantity": 4.0},
    )
    get_response = await client.get(f"/api/v1/orders/{order['id']}")
    assert get_response.json()["total"] == "20.0000"  # 4 × 5.00


@pytest.mark.asyncio
async def test_add_item_below_minimum_quantity(client: AsyncClient) -> None:
    supplier = await _create_supplier(client, "Min Qty Supplier")
    product = await _create_product(client, "Spring C", "SPR-C")
    await _link_product(client, supplier["id"], product["id"], min_qty=10.0)
    order = await _create_order(client, supplier["id"])

    response = await client.post(
        f"/api/v1/orders/{order['id']}/items",
        json={"product_id": product["id"], "quantity": 3.0},  # below minimum
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_add_item_not_sold_by_supplier(client: AsyncClient) -> None:
    supplier = await _create_supplier(client, "Wrong Supplier")
    product = await _create_product(client, "Widget D", "WGT-D")
    # Product NOT linked to supplier
    order = await _create_order(client, supplier["id"])

    response = await client.post(
        f"/api/v1/orders/{order['id']}/items",
        json={"product_id": product["id"], "quantity": 10.0},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_add_duplicate_item(client: AsyncClient) -> None:
    supplier = await _create_supplier(client, "Dup Item Supplier")
    product = await _create_product(client, "Pipe E", "PIPE-E")
    await _link_product(client, supplier["id"], product["id"], min_qty=1.0)
    order = await _create_order(client, supplier["id"])
    payload = {"product_id": product["id"], "quantity": 5.0}
    await client.post(f"/api/v1/orders/{order['id']}/items", json=payload)
    response = await client.post(f"/api/v1/orders/{order['id']}/items", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_update_item_quantity(client: AsyncClient) -> None:
    supplier = await _create_supplier(client, "Update Item Supplier")
    product = await _create_product(client, "Rod F", "ROD-F")
    await _link_product(client, supplier["id"], product["id"], min_qty=2.0, unit_price="3.00")
    order = await _create_order(client, supplier["id"])
    await client.post(
        f"/api/v1/orders/{order['id']}/items",
        json={"product_id": product["id"], "quantity": 5.0},
    )
    response = await client.patch(
        f"/api/v1/orders/{order['id']}/items/{product['id']}",
        json={"quantity": 10.0},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["quantity"] == 10.0
    assert data["subtotal"] == "30.0000"  # 10 × 3.00


@pytest.mark.asyncio
async def test_remove_item(client: AsyncClient) -> None:
    supplier = await _create_supplier(client, "Remove Item Supplier")
    product = await _create_product(client, "Valve G", "VLV-G")
    await _link_product(client, supplier["id"], product["id"], min_qty=1.0)
    order = await _create_order(client, supplier["id"])
    await client.post(
        f"/api/v1/orders/{order['id']}/items",
        json={"product_id": product["id"], "quantity": 5.0},
    )
    response = await client.delete(
        f"/api/v1/orders/{order['id']}/items/{product['id']}"
    )
    assert response.status_code == 204

    get_response = await client.get(f"/api/v1/orders/{order['id']}")
    assert get_response.json()["items"] == []
    assert get_response.json()["total"] == "0.0000"


@pytest.mark.asyncio
async def test_confirm_snapshots_price(client: AsyncClient) -> None:
    supplier = await _create_supplier(client, "Snapshot Supplier")
    product = await _create_product(client, "Cap H", "CAP-H")
    await _link_product(client, supplier["id"], product["id"], min_qty=1.0, unit_price="7.00")
    order = await _create_order(client, supplier["id"])
    await client.post(
        f"/api/v1/orders/{order['id']}/items",
        json={"product_id": product["id"], "quantity": 3.0},
    )

    response = await client.patch(
        f"/api/v1/orders/{order['id']}/status", json={"status": "CONFIRMED"}
    )
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["unit_price"] == "7.0000"    # price snapshotted
    assert items[0]["subtotal"] == "21.0000"     # 3 × 7.00
    assert response.json()["total"] == "21.0000"


@pytest.mark.asyncio
async def test_add_item_to_confirmed_order_fails(client: AsyncClient) -> None:
    supplier = await _create_supplier(client, "Locked Supplier")
    product = await _create_product(client, "Ring I", "RNG-I")
    await _link_product(client, supplier["id"], product["id"], min_qty=1.0)
    order = await _create_order(client, supplier["id"])
    await client.patch(f"/api/v1/orders/{order['id']}/status", json={"status": "CONFIRMED"})

    response = await client.post(
        f"/api/v1/orders/{order['id']}/items",
        json={"product_id": product["id"], "quantity": 5.0},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_cancel_order(client: AsyncClient) -> None:
    supplier = await _create_supplier(client, "Cancel Supplier")
    order = await _create_order(client, supplier["id"])
    response = await client.patch(
        f"/api/v1/orders/{order['id']}/status", json={"status": "CANCELLED"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "CANCELLED"
