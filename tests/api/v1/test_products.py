import io

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


# ── CSV import ────────────────────────────────────────────────────────────────

def _csv_file(content: str, filename: str = "products.csv") -> tuple:
    return ("file", (filename, io.BytesIO(content.encode()), "text/csv"))


@pytest.mark.asyncio
async def test_import_csv_happy_path(client: AsyncClient) -> None:
    csv_content = "name,sku,description,unit\nGadget X,CSV-001,A gadget,pcs\nTool Y,CSV-002,,kg\n"
    response = await client.post(
        "/api/v1/products/import",
        files=[_csv_file(csv_content)],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_rows"] == 2
    assert data["imported"] == 2
    assert data["updated"] == 0
    assert data["errors"] == 0
    assert data["rows"][0]["status"] == "imported"
    assert data["rows"][0]["sku"] == "CSV-001"


@pytest.mark.asyncio
async def test_import_csv_upsert(client: AsyncClient) -> None:
    # First import — creates the product
    csv_v1 = "name,sku\nOld Name,UPSERT-001\n"
    await client.post("/api/v1/products/import", files=[_csv_file(csv_v1)])

    # Second import — updates the product
    csv_v2 = "name,sku\nNew Name,UPSERT-001\n"
    response = await client.post("/api/v1/products/import", files=[_csv_file(csv_v2)])
    assert response.status_code == 200
    data = response.json()
    assert data["updated"] == 1
    assert data["imported"] == 0
    assert data["rows"][0]["status"] == "updated"
    assert data["rows"][0]["name"] == "New Name"

    # Confirm DB reflects the update
    products = await client.get("/api/v1/products")
    names = [p["name"] for p in products.json() if p["sku"] == "UPSERT-001"]
    assert names == ["New Name"]


@pytest.mark.asyncio
async def test_import_csv_with_row_errors(client: AsyncClient) -> None:
    csv_content = (
        "name,sku\n"
        "Good Product,ERR-001\n"
        ",ERR-002\n"          # missing name — should error
        "Another Good,ERR-003\n"
    )
    response = await client.post(
        "/api/v1/products/import",
        files=[_csv_file(csv_content)],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["imported"] == 2
    assert data["errors"] == 1
    error_row = next(r for r in data["rows"] if r["status"] == "error")
    assert error_row["row"] == 2
    assert error_row["reason"] is not None


@pytest.mark.asyncio
async def test_import_csv_missing_required_header(client: AsyncClient) -> None:
    csv_content = "product_name,code\nWidget,W-001\n"  # wrong headers
    response = await client.post(
        "/api/v1/products/import",
        files=[_csv_file(csv_content)],
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_import_csv_wrong_file_type(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/products/import",
        files=[_csv_file("some content", filename="products.txt")],
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_import_csv_bom_encoding(client: AsyncClient) -> None:
    # UTF-8 BOM prefix — common from Excel exports
    csv_content = "\ufeffname,sku\nBOM Product,BOM-001\n"
    response = await client.post(
        "/api/v1/products/import",
        files=[_csv_file(csv_content)],  # _csv_file handles encoding
    )
    assert response.status_code == 200
    assert response.json()["imported"] == 1


@pytest.mark.asyncio
async def test_import_csv_empty_rows_ignored(client: AsyncClient) -> None:
    csv_content = "name,sku\nReal Product,REAL-001\n\n   \n"
    response = await client.post(
        "/api/v1/products/import",
        files=[_csv_file(csv_content)],
    )
    assert response.status_code == 200
    assert response.json()["total_rows"] == 1  # empty rows not counted
