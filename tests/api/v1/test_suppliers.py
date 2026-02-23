import pytest
from httpx import AsyncClient


# ── Helper ────────────────────────────────────────────────────────────────────

async def _create_supplier(client: AsyncClient, name: str, suffix: str = "") -> dict:
    resp = await client.post(
        "/api/v1/suppliers",
        json={"name": name, "email": f"contact{suffix}@example.com", "phone": "555-0100"},
    )
    assert resp.status_code == 201
    return resp.json()


async def _create_product(client: AsyncClient, name: str, sku: str) -> dict:
    resp = await client.post("/api/v1/products", json={"name": name, "sku": sku})
    assert resp.status_code == 201
    return resp.json()


# ── Supplier CRUD ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_supplier(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/suppliers",
        json={"name": "Acme Corp", "email": "acme@example.com", "phone": "555-1234"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Acme Corp"
    assert data["email"] == "acme@example.com"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_supplier_duplicate_name(client: AsyncClient) -> None:
    await client.post("/api/v1/suppliers", json={"name": "Dup Supplier"})
    response = await client.post("/api/v1/suppliers", json={"name": "Dup Supplier"})
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_list_suppliers(client: AsyncClient) -> None:
    await _create_supplier(client, "List Supplier 1", "1")
    await _create_supplier(client, "List Supplier 2", "2")
    response = await client.get("/api/v1/suppliers")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_supplier_with_empty_products(client: AsyncClient) -> None:
    supplier = await _create_supplier(client, "Empty Supplier", "empty")
    response = await client.get(f"/api/v1/suppliers/{supplier['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == supplier["id"]
    assert data["supplier_products"] == []


@pytest.mark.asyncio
async def test_get_supplier_not_found(client: AsyncClient) -> None:
    response = await client.get("/api/v1/suppliers/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_supplier(client: AsyncClient) -> None:
    supplier = await _create_supplier(client, "Before Update", "upd")
    response = await client.patch(
        f"/api/v1/suppliers/{supplier['id']}",
        json={"name": "After Update", "address": "123 Main St"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "After Update"
    assert data["address"] == "123 Main St"


@pytest.mark.asyncio
async def test_delete_supplier(client: AsyncClient) -> None:
    supplier = await _create_supplier(client, "To Be Deleted", "del")
    response = await client.delete(f"/api/v1/suppliers/{supplier['id']}")
    assert response.status_code == 204
    get_response = await client.get(f"/api/v1/suppliers/{supplier['id']}")
    assert get_response.status_code == 404


# ── Supplier-Product management ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_add_product_to_supplier(client: AsyncClient) -> None:
    supplier = await _create_supplier(client, "Supplier With Products", "wp")
    product = await _create_product(client, "Bolt M8", "BOLT-M8")

    response = await client.post(
        f"/api/v1/suppliers/{supplier['id']}/products",
        json={
            "product_id": product["id"],
            "minimum_quantity": 10.0,
            "optimal_quantity": 50.0,
            "unit_price": "1.25",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["product_id"] == product["id"]
    assert data["minimum_quantity"] == 10.0
    assert data["optimal_quantity"] == 50.0
    assert data["product"]["sku"] == "BOLT-M8"


@pytest.mark.asyncio
async def test_add_duplicate_product_to_supplier(client: AsyncClient) -> None:
    supplier = await _create_supplier(client, "Supplier Dup Product", "dp")
    product = await _create_product(client, "Nut M8", "NUT-M8")

    payload = {"product_id": product["id"], "minimum_quantity": 5.0, "optimal_quantity": 20.0}
    await client.post(f"/api/v1/suppliers/{supplier['id']}/products", json=payload)
    response = await client.post(f"/api/v1/suppliers/{supplier['id']}/products", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_add_nonexistent_product_to_supplier(client: AsyncClient) -> None:
    supplier = await _create_supplier(client, "Supplier Ghost Product", "gp")
    response = await client.post(
        f"/api/v1/suppliers/{supplier['id']}/products",
        json={
            "product_id": "00000000-0000-0000-0000-000000000000",
            "minimum_quantity": 1.0,
            "optimal_quantity": 5.0,
        },
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_supplier_products(client: AsyncClient) -> None:
    supplier = await _create_supplier(client, "Supplier List Products", "lp")
    product1 = await _create_product(client, "Screw M4", "SCR-M4")
    product2 = await _create_product(client, "Washer M4", "WSH-M4")

    for p in [product1, product2]:
        await client.post(
            f"/api/v1/suppliers/{supplier['id']}/products",
            json={"product_id": p["id"], "minimum_quantity": 1.0, "optimal_quantity": 10.0},
        )

    response = await client.get(f"/api/v1/suppliers/{supplier['id']}/products")
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_update_supplier_product(client: AsyncClient) -> None:
    supplier = await _create_supplier(client, "Supplier Update SP", "usp")
    product = await _create_product(client, "Cable 1m", "CBL-1M")

    await client.post(
        f"/api/v1/suppliers/{supplier['id']}/products",
        json={"product_id": product["id"], "minimum_quantity": 5.0, "optimal_quantity": 20.0},
    )
    response = await client.patch(
        f"/api/v1/suppliers/{supplier['id']}/products/{product['id']}",
        json={"optimal_quantity": 100.0, "unit_price": "3.50"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["optimal_quantity"] == 100.0
    assert data["minimum_quantity"] == 5.0


@pytest.mark.asyncio
async def test_remove_product_from_supplier(client: AsyncClient) -> None:
    supplier = await _create_supplier(client, "Supplier Remove SP", "rsp")
    product = await _create_product(client, "Gear Z10", "GR-Z10")

    await client.post(
        f"/api/v1/suppliers/{supplier['id']}/products",
        json={"product_id": product["id"], "minimum_quantity": 1.0, "optimal_quantity": 5.0},
    )
    response = await client.delete(
        f"/api/v1/suppliers/{supplier['id']}/products/{product['id']}"
    )
    assert response.status_code == 204

    list_response = await client.get(f"/api/v1/suppliers/{supplier['id']}/products")
    assert list_response.json() == []


@pytest.mark.asyncio
async def test_get_supplier_shows_linked_products(client: AsyncClient) -> None:
    supplier = await _create_supplier(client, "Supplier Full View", "fv")
    product = await _create_product(client, "Spring S1", "SPR-S1")

    await client.post(
        f"/api/v1/suppliers/{supplier['id']}/products",
        json={"product_id": product["id"], "minimum_quantity": 2.0, "optimal_quantity": 15.0},
    )
    response = await client.get(f"/api/v1/suppliers/{supplier['id']}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["supplier_products"]) == 1
    assert data["supplier_products"][0]["product"]["sku"] == "SPR-S1"
