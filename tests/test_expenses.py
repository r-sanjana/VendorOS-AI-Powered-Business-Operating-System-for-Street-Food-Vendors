"""
VendorOS - Tests: Expense Management
Covers expense CRUD + analytics endpoints.
"""

from datetime import date

import pytest
from httpx import AsyncClient

from tests.conftest import auth_headers

pytestmark = pytest.mark.asyncio


async def _create_vendor(client: AsyncClient, token: str) -> str:
    resp = await client.post(
        "/api/v1/vendors",
        json={"business_name": "Expense Test Stall", "owner_name": "Owner"},
        headers=auth_headers(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _expense_payload(vendor_id: str, category: str = "RAW_MATERIALS", amount: str = "500.00") -> dict:
    return {
        "vendor_id": vendor_id,
        "expense_date": str(date.today()),
        "category": category,
        "amount": amount,
        "description": f"Test {category} expense",
    }


class TestCreateExpense:
    """POST /api/v1/expenses"""

    async def test_create_expense_success(
        self, client: AsyncClient, vendor_token: str
    ) -> None:
        vendor_id = await _create_vendor(client, vendor_token)
        resp = await client.post(
            "/api/v1/expenses",
            json=_expense_payload(vendor_id),
            headers=auth_headers(vendor_token),
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert float(data["amount"]) == 500.0
        assert data["category"] == "RAW_MATERIALS"
        assert data["vendor_id"] == vendor_id

    async def test_create_expense_negative_amount_rejected(
        self, client: AsyncClient, vendor_token: str
    ) -> None:
        vendor_id = await _create_vendor(client, vendor_token)
        payload = _expense_payload(vendor_id)
        payload["amount"] = "-100.00"
        resp = await client.post(
            "/api/v1/expenses",
            json=payload,
            headers=auth_headers(vendor_token),
        )
        assert resp.status_code == 422

    async def test_create_expense_requires_auth(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/expenses",
            json={"vendor_id": "irrelevant", "expense_date": str(date.today()),
                  "category": "GAS", "amount": "100"},
        )
        assert resp.status_code == 403


class TestListExpenses:
    """GET /api/v1/expenses"""

    async def test_list_expenses_for_vendor(
        self, client: AsyncClient, vendor_token: str
    ) -> None:
        vendor_id = await _create_vendor(client, vendor_token)
        for cat in ["GAS", "RENT", "SALARY"]:
            await client.post(
                "/api/v1/expenses",
                json=_expense_payload(vendor_id, category=cat),
                headers=auth_headers(vendor_token),
            )

        resp = await client.get(
            f"/api/v1/expenses?vendor_id={vendor_id}",
            headers=auth_headers(vendor_token),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 3
        assert len(body["items"]) == 3

    async def test_list_expenses_filter_by_category(
        self, client: AsyncClient, vendor_token: str
    ) -> None:
        vendor_id = await _create_vendor(client, vendor_token)
        for cat in ["GAS", "GAS", "ELECTRICITY"]:
            await client.post(
                "/api/v1/expenses",
                json=_expense_payload(vendor_id, category=cat),
                headers=auth_headers(vendor_token),
            )

        resp = await client.get(
            f"/api/v1/expenses?vendor_id={vendor_id}&category=GAS",
            headers=auth_headers(vendor_token),
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 2

    async def test_list_expenses_pagination(
        self, client: AsyncClient, vendor_token: str
    ) -> None:
        vendor_id = await _create_vendor(client, vendor_token)
        for _ in range(5):
            await client.post(
                "/api/v1/expenses",
                json=_expense_payload(vendor_id),
                headers=auth_headers(vendor_token),
            )

        resp = await client.get(
            f"/api/v1/expenses?vendor_id={vendor_id}&page=1&size=2",
            headers=auth_headers(vendor_token),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["items"]) == 2
        assert body["total"] == 5
        assert body["pages"] == 3


class TestGetExpense:
    """GET /api/v1/expenses/{id}"""

    async def test_get_expense_by_id(
        self, client: AsyncClient, vendor_token: str
    ) -> None:
        vendor_id = await _create_vendor(client, vendor_token)
        create = await client.post(
            "/api/v1/expenses",
            json=_expense_payload(vendor_id, "TRANSPORTATION"),
            headers=auth_headers(vendor_token),
        )
        expense_id = create.json()["id"]

        resp = await client.get(
            f"/api/v1/expenses/{expense_id}",
            headers=auth_headers(vendor_token),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == expense_id
        assert resp.json()["category"] == "TRANSPORTATION"

    async def test_get_expense_not_found(
        self, client: AsyncClient, vendor_token: str
    ) -> None:
        resp = await client.get(
            "/api/v1/expenses/00000000-0000-0000-0000-000000000000",
            headers=auth_headers(vendor_token),
        )
        assert resp.status_code == 404


class TestUpdateExpense:
    """PUT /api/v1/expenses/{id}"""

    async def test_update_expense(
        self, client: AsyncClient, vendor_token: str
    ) -> None:
        vendor_id = await _create_vendor(client, vendor_token)
        create = await client.post(
            "/api/v1/expenses",
            json=_expense_payload(vendor_id, "MAINTENANCE", "200.00"),
            headers=auth_headers(vendor_token),
        )
        expense_id = create.json()["id"]

        resp = await client.put(
            f"/api/v1/expenses/{expense_id}",
            json={"amount": "350.00", "description": "Updated description"},
            headers=auth_headers(vendor_token),
        )
        assert resp.status_code == 200
        assert float(resp.json()["amount"]) == 350.0
        assert resp.json()["description"] == "Updated description"

    async def test_update_nonexistent_expense(
        self, client: AsyncClient, vendor_token: str
    ) -> None:
        resp = await client.put(
            "/api/v1/expenses/00000000-0000-0000-0000-000000000000",
            json={"amount": "100.00"},
            headers=auth_headers(vendor_token),
        )
        assert resp.status_code == 404


class TestDeleteExpense:
    """DELETE /api/v1/expenses/{id}"""

    async def test_delete_expense(
        self, client: AsyncClient, vendor_token: str
    ) -> None:
        vendor_id = await _create_vendor(client, vendor_token)
        create = await client.post(
            "/api/v1/expenses",
            json=_expense_payload(vendor_id),
            headers=auth_headers(vendor_token),
        )
        expense_id = create.json()["id"]

        resp = await client.delete(
            f"/api/v1/expenses/{expense_id}",
            headers=auth_headers(vendor_token),
        )
        assert resp.status_code == 204

        confirm = await client.get(
            f"/api/v1/expenses/{expense_id}",
            headers=auth_headers(vendor_token),
        )
        assert confirm.status_code == 404


class TestExpenseAnalytics:
    """GET /api/v1/expenses/analytics"""

    async def test_analytics_by_category(
        self, client: AsyncClient, vendor_token: str
    ) -> None:
        vendor_id = await _create_vendor(client, vendor_token)
        today = str(date.today())

        expenses = [
            ("RAW_MATERIALS", "1000.00"),
            ("RAW_MATERIALS", "500.00"),
            ("GAS", "300.00"),
            ("ELECTRICITY", "200.00"),
        ]
        for cat, amt in expenses:
            await client.post(
                "/api/v1/expenses",
                json=_expense_payload(vendor_id, cat, amt),
                headers=auth_headers(vendor_token),
            )

        resp = await client.get(
            f"/api/v1/expenses/analytics"
            f"?vendor_id={vendor_id}&start_date={today}&end_date={today}",
            headers=auth_headers(vendor_token),
        )
        assert resp.status_code == 200
        rows = resp.json()

        # RAW_MATERIALS should be first (highest total = 1500)
        assert rows[0]["category"] == "RAW_MATERIALS"
        assert float(rows[0]["total_amount"]) == 1500.0
        assert rows[0]["transaction_count"] == 2

        # All percentages should sum to ~100
        total_pct = sum(r["percentage_of_total"] for r in rows)
        assert abs(total_pct - 100.0) < 0.5