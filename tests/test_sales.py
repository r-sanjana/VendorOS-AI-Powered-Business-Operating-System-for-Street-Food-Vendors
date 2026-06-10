"""
VendorOS - Tests: Sales Management
Covers sale creation, retrieval, and revenue analytics.
"""

from datetime import date

import pytest
from httpx import AsyncClient

from tests.conftest import auth_headers

pytestmark = pytest.mark.asyncio


async def _create_vendor(client: AsyncClient, token: str) -> str:
    resp = await client.post(
        "/api/v1/vendors",
        json={"business_name": "Sales Test Stall", "owner_name": "Vendor"},
        headers=auth_headers(token),
    )
    return resp.json()["id"]


def _sale_payload(vendor_id: str, sale_date: str | None = None) -> dict:
    return {
        "vendor_id": vendor_id,
        "sale_date": sale_date or str(date.today()),
        "payment_method": "UPI",
        "items": [
            {"item_name": "Masala Dosa", "quantity": 3, "unit_price": "60.00"},
            {"item_name": "Filter Coffee", "quantity": 3, "unit_price": "20.00"},
        ],
    }


class TestCreateSale:
    """POST /api/v1/sales"""

    async def test_create_sale_success(
        self, client: AsyncClient, vendor_token: str
    ) -> None:
        vendor_id = await _create_vendor(client, vendor_token)
        resp = await client.post(
            "/api/v1/sales",
            json=_sale_payload(vendor_id),
            headers=auth_headers(vendor_token),
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert float(data["total_amount"]) == 240.0   # (3×60) + (3×20)
        assert len(data["items"]) == 2
        assert data["payment_method"] == "UPI"

    async def test_create_sale_empty_items_rejected(
        self, client: AsyncClient, vendor_token: str
    ) -> None:
        vendor_id = await _create_vendor(client, vendor_token)
        payload = _sale_payload(vendor_id)
        payload["items"] = []
        resp = await client.post(
            "/api/v1/sales",
            json=payload,
            headers=auth_headers(vendor_token),
        )
        assert resp.status_code == 422


class TestGetSale:
    """GET /api/v1/sales/{id}"""

    async def test_get_sale_by_id(
        self, client: AsyncClient, vendor_token: str
    ) -> None:
        vendor_id = await _create_vendor(client, vendor_token)
        create = await client.post(
            "/api/v1/sales",
            json=_sale_payload(vendor_id),
            headers=auth_headers(vendor_token),
        )
        sale_id = create.json()["id"]
        resp = await client.get(
            f"/api/v1/sales/{sale_id}",
            headers=auth_headers(vendor_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == sale_id

    async def test_get_sale_not_found(
        self, client: AsyncClient, vendor_token: str
    ) -> None:
        resp = await client.get(
            "/api/v1/sales/00000000-0000-0000-0000-000000000000",
            headers=auth_headers(vendor_token),
        )
        assert resp.status_code == 404


class TestSalesAnalytics:
    """GET /api/v1/sales/analytics/revenue  |  /top-products"""

    async def test_revenue_summary(
        self, client: AsyncClient, vendor_token: str
    ) -> None:
        vendor_id = await _create_vendor(client, vendor_token)
        today = str(date.today())

        # Record two sales
        for _ in range(2):
            await client.post(
                "/api/v1/sales",
                json=_sale_payload(vendor_id, today),
                headers=auth_headers(vendor_token),
            )

        resp = await client.get(
            f"/api/v1/sales/analytics/revenue"
            f"?vendor_id={vendor_id}&start_date={today}&end_date={today}",
            headers=auth_headers(vendor_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert float(data["total_revenue"]) == 480.0   # 2 × 240
        assert data["transaction_count"] == 2

    async def test_top_products(
        self, client: AsyncClient, vendor_token: str
    ) -> None:
        vendor_id = await _create_vendor(client, vendor_token)
        today = str(date.today())
        await client.post(
            "/api/v1/sales",
            json=_sale_payload(vendor_id, today),
            headers=auth_headers(vendor_token),
        )

        resp = await client.get(
            f"/api/v1/sales/analytics/top-products"
            f"?vendor_id={vendor_id}&start_date={today}&end_date={today}&top_n=5",
            headers=auth_headers(vendor_token),
        )
        assert resp.status_code == 200
        items = resp.json()
        assert len(items) >= 1
        assert items[0]["item_name"] == "Masala Dosa"