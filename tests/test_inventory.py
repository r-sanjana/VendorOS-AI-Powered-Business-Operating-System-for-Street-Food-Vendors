"""
VendorOS - Tests: Inventory Management
Covers inventory CRUD + stock movement + low-stock alerts.
"""

import pytest
from httpx import AsyncClient

from tests.conftest import auth_headers

pytestmark = pytest.mark.asyncio


async def _create_vendor(client: AsyncClient, token: str) -> str:
    """Helper: create a vendor and return its ID."""
    resp = await client.post(
        "/api/v1/vendors",
        json={
            "business_name": "Test Stall",
            "owner_name": "Test Owner",
            "city": "Mysuru",
            "state": "Karnataka",
        },
        headers=auth_headers(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


class TestInventoryCRUD:
    """POST/GET/PUT/DELETE /api/v1/inventory"""

    async def test_create_inventory_item(
        self, client: AsyncClient, vendor_token: str
    ) -> None:
        vendor_id = await _create_vendor(client, vendor_token)
        resp = await client.post(
            "/api/v1/inventory",
            json={
                "vendor_id": vendor_id,
                "name": "Basmati Rice",
                "category": "RICE",
                "unit": "kg",
                "current_stock": "50.000",
                "reorder_level": "10.000",
                "cost_per_unit": "80.00",
            },
            headers=auth_headers(vendor_token),
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["name"] == "Basmati Rice"
        assert data["category"] == "RICE"
        assert data["is_low_stock"] is False

    async def test_list_inventory_items(
        self, client: AsyncClient, vendor_token: str
    ) -> None:
        vendor_id = await _create_vendor(client, vendor_token)
        for name in ["Rice", "Oil"]:
            await client.post(
                "/api/v1/inventory",
                json={
                    "vendor_id": vendor_id,
                    "name": name,
                    "category": "OTHER",
                    "unit": "kg",
                    "current_stock": "5",
                    "reorder_level": "1",
                    "cost_per_unit": "10",
                },
                headers=auth_headers(vendor_token),
            )
        resp = await client.get(
            f"/api/v1/inventory?vendor_id={vendor_id}",
            headers=auth_headers(vendor_token),
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 2

    async def test_update_inventory_item(
        self, client: AsyncClient, vendor_token: str
    ) -> None:
        vendor_id = await _create_vendor(client, vendor_token)
        create = await client.post(
            "/api/v1/inventory",
            json={
                "vendor_id": vendor_id,
                "name": "Sunflower Oil",
                "category": "OIL",
                "unit": "litre",
                "current_stock": "20",
                "reorder_level": "5",
                "cost_per_unit": "120",
            },
            headers=auth_headers(vendor_token),
        )
        item_id = create.json()["id"]
        resp = await client.put(
            f"/api/v1/inventory/{item_id}",
            json={"current_stock": "30", "cost_per_unit": "125"},
            headers=auth_headers(vendor_token),
        )
        assert resp.status_code == 200
        assert float(resp.json()["current_stock"]) == 30.0

    async def test_delete_inventory_item(
        self, client: AsyncClient, vendor_token: str
    ) -> None:
        vendor_id = await _create_vendor(client, vendor_token)
        create = await client.post(
            "/api/v1/inventory",
            json={
                "vendor_id": vendor_id,
                "name": "To Delete",
                "category": "OTHER",
                "unit": "kg",
                "current_stock": "1",
                "reorder_level": "0",
                "cost_per_unit": "10",
            },
            headers=auth_headers(vendor_token),
        )
        item_id = create.json()["id"]
        resp = await client.delete(
            f"/api/v1/inventory/{item_id}",
            headers=auth_headers(vendor_token),
        )
        assert resp.status_code == 204


class TestStockMovements:
    """POST /api/v1/inventory/movements"""

    async def test_stock_in_increases_stock(
        self, client: AsyncClient, vendor_token: str
    ) -> None:
        vendor_id = await _create_vendor(client, vendor_token)
        item = await client.post(
            "/api/v1/inventory",
            json={
                "vendor_id": vendor_id,
                "name": "Chicken",
                "category": "CHICKEN",
                "unit": "kg",
                "current_stock": "10",
                "reorder_level": "2",
                "cost_per_unit": "250",
            },
            headers=auth_headers(vendor_token),
        )
        item_id = item.json()["id"]
        await client.post(
            "/api/v1/inventory/movements",
            json={"item_id": item_id, "movement_type": "IN", "quantity": "5.0"},
            headers=auth_headers(vendor_token),
        )
        resp = await client.get(
            f"/api/v1/inventory/{item_id}",
            headers=auth_headers(vendor_token),
        )
        assert float(resp.json()["current_stock"]) == 15.0

    async def test_stock_out_decreases_stock(
        self, client: AsyncClient, vendor_token: str
    ) -> None:
        vendor_id = await _create_vendor(client, vendor_token)
        item = await client.post(
            "/api/v1/inventory",
            json={
                "vendor_id": vendor_id,
                "name": "Spices",
                "category": "SPICES",
                "unit": "kg",
                "current_stock": "8",
                "reorder_level": "1",
                "cost_per_unit": "400",
            },
            headers=auth_headers(vendor_token),
        )
        item_id = item.json()["id"]
        await client.post(
            "/api/v1/inventory/movements",
            json={"item_id": item_id, "movement_type": "OUT", "quantity": "3.0"},
            headers=auth_headers(vendor_token),
        )
        resp = await client.get(
            f"/api/v1/inventory/{item_id}",
            headers=auth_headers(vendor_token),
        )
        assert float(resp.json()["current_stock"]) == 5.0


class TestLowStockAlerts:
    """GET /api/v1/inventory/low-stock"""

    async def test_low_stock_detected(
        self, client: AsyncClient, vendor_token: str
    ) -> None:
        vendor_id = await _create_vendor(client, vendor_token)
        # Item below reorder level
        await client.post(
            "/api/v1/inventory",
            json={
                "vendor_id": vendor_id,
                "name": "Packaging Boxes",
                "category": "PACKAGING",
                "unit": "piece",
                "current_stock": "2",
                "reorder_level": "10",
                "cost_per_unit": "5",
            },
            headers=auth_headers(vendor_token),
        )
        resp = await client.get(
            f"/api/v1/inventory/low-stock?vendor_id={vendor_id}",
            headers=auth_headers(vendor_token),
        )
        assert resp.status_code == 200
        items = resp.json()
        assert len(items) == 1
        assert items[0]["item_name"] == "Packaging Boxes"