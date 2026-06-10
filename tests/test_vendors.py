"""
VendorOS - Tests: Vendor Management
Covers POST/GET/PUT/DELETE /vendors.
"""

import pytest
from httpx import AsyncClient

from tests.conftest import auth_headers

pytestmark = pytest.mark.asyncio

VENDOR_PAYLOAD = {
    "business_name": "Ravi's Dosa Corner",
    "owner_name": "Ravi Kumar",
    "phone": "+919876543210",
    "email": "ravi.dosa@test.com",
    "address": "MG Road",
    "city": "Mysuru",
    "state": "Karnataka",
    "latitude": "12.295810",
    "longitude": "76.639381",
    "fssai_number": "12345678901234",
    "gst_number": "29ABCDE1234F1Z5",
}


class TestCreateVendor:
    """POST /api/v1/vendors"""

    async def test_create_vendor_success(
        self, client: AsyncClient, vendor_token: str
    ) -> None:
        resp = await client.post(
            "/api/v1/vendors",
            json=VENDOR_PAYLOAD,
            headers=auth_headers(vendor_token),
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["business_name"] == "Ravi's Dosa Corner"
        assert data["city"] == "Mysuru"
        assert "id" in data

    async def test_create_vendor_requires_auth(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/vendors", json=VENDOR_PAYLOAD)
        assert resp.status_code == 403


class TestListVendors:
    """GET /api/v1/vendors"""

    async def test_list_vendors(
        self, client: AsyncClient, vendor_token: str
    ) -> None:
        # Create two vendors
        for i in range(2):
            p = {**VENDOR_PAYLOAD, "business_name": f"Shop {i}", "email": f"shop{i}@test.com"}
            await client.post("/api/v1/vendors", json=p, headers=auth_headers(vendor_token))

        resp = await client.get(
            "/api/v1/vendors", headers=auth_headers(vendor_token)
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 2
        assert "items" in body

    async def test_list_vendors_pagination(
        self, client: AsyncClient, vendor_token: str
    ) -> None:
        resp = await client.get(
            "/api/v1/vendors?page=1&size=1",
            headers=auth_headers(vendor_token),
        )
        assert resp.status_code == 200
        assert resp.json()["size"] == 1


class TestGetVendor:
    """GET /api/v1/vendors/{id}"""

    async def test_get_vendor_by_id(
        self, client: AsyncClient, vendor_token: str
    ) -> None:
        create = await client.post(
            "/api/v1/vendors", json=VENDOR_PAYLOAD, headers=auth_headers(vendor_token)
        )
        vendor_id = create.json()["id"]
        resp = await client.get(
            f"/api/v1/vendors/{vendor_id}", headers=auth_headers(vendor_token)
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == vendor_id

    async def test_get_vendor_not_found(
        self, client: AsyncClient, vendor_token: str
    ) -> None:
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.get(
            f"/api/v1/vendors/{fake_id}", headers=auth_headers(vendor_token)
        )
        assert resp.status_code == 404


class TestUpdateVendor:
    """PUT /api/v1/vendors/{id}"""

    async def test_update_vendor(
        self, client: AsyncClient, vendor_token: str
    ) -> None:
        create = await client.post(
            "/api/v1/vendors", json=VENDOR_PAYLOAD, headers=auth_headers(vendor_token)
        )
        vendor_id = create.json()["id"]
        resp = await client.put(
            f"/api/v1/vendors/{vendor_id}",
            json={"city": "Bengaluru", "business_name": "Updated Dosa Corner"},
            headers=auth_headers(vendor_token),
        )
        assert resp.status_code == 200
        assert resp.json()["city"] == "Bengaluru"
        assert resp.json()["business_name"] == "Updated Dosa Corner"


class TestDeleteVendor:
    """DELETE /api/v1/vendors/{id}"""

    async def test_delete_vendor(
        self, client: AsyncClient, vendor_token: str
    ) -> None:
        create = await client.post(
            "/api/v1/vendors", json=VENDOR_PAYLOAD, headers=auth_headers(vendor_token)
        )
        vendor_id = create.json()["id"]
        resp = await client.delete(
            f"/api/v1/vendors/{vendor_id}", headers=auth_headers(vendor_token)
        )
        assert resp.status_code == 204

        # Confirm it's gone
        get = await client.get(
            f"/api/v1/vendors/{vendor_id}", headers=auth_headers(vendor_token)
        )
        assert get.status_code == 404