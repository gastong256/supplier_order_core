import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_product(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/products",
        json={"name": "Widget A", "sku": "WGT-001", "description": "A small widget", "unit": "pcs"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Widget A"
    assert data["sku"] == "WGT-001"
    assert data["unit"] == "pcs"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_product_duplicate_sku(client: AsyncClient) -> None:
    await client.post("/api/v1/products", json={"name": "Widget B", "sku": "WGT-DUP"})
    response = await client.post("/api/v1/products", json={"name": "Widget C", "sku": "WGT-DUP"})
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_list_products(client: AsyncClient) -> None:
    await client.post("/api/v1/products", json={"name": "Product List 1", "sku": "LST-001"})
    await client.post("/api/v1/products", json={"name": "Product List 2", "sku": "LST-002"})
    response = await client.get("/api/v1/products")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_product(client: AsyncClient) -> None:
    created = await client.post(
        "/api/v1/products", json={"name": "Get Me", "sku": "GET-001"}
    )
    product_id = created.json()["id"]
    response = await client.get(f"/api/v1/products/{product_id}")
    assert response.status_code == 200
    assert response.json()["id"] == product_id


@pytest.mark.asyncio
async def test_get_product_not_found(client: AsyncClient) -> None:
    response = await client.get("/api/v1/products/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_product(client: AsyncClient) -> None:
    created = await client.post(
        "/api/v1/products", json={"name": "Old Name", "sku": "UPD-001"}
    )
    product_id = created.json()["id"]
    response = await client.patch(
        f"/api/v1/products/{product_id}", json={"name": "New Name"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"
    assert response.json()["sku"] == "UPD-001"


@pytest.mark.asyncio
async def test_delete_product(client: AsyncClient) -> None:
    created = await client.post(
        "/api/v1/products", json={"name": "Delete Me", "sku": "DEL-001"}
    )
    product_id = created.json()["id"]
    response = await client.delete(f"/api/v1/products/{product_id}")
    assert response.status_code == 204
    get_response = await client.get(f"/api/v1/products/{product_id}")
    assert get_response.status_code == 404
