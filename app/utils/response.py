"""
VendorOS - Utility: Response Helpers
Standardised success / error envelope builders used across all routes.
"""

import math
from typing import Any, Generic, List, Optional, TypeVar

from fastapi.responses import JSONResponse
from pydantic import BaseModel

T = TypeVar("T")


# ── Standard envelope ──────────────────────────────────────────────────────────

def success_response(
    data: Any,
    message: str = "Success",
    status_code: int = 200,
) -> JSONResponse:
    """
    Wrap *data* in a consistent ``{success, message, data}`` envelope.

    Usage::

        return success_response(vendor_schema, "Vendor created", 201)
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "message": message,
            "data": data,
        },
    )


def error_response(
    message: str,
    status_code: int = 400,
    detail: Optional[Any] = None,
) -> JSONResponse:
    """Return a standardised error envelope."""
    body: dict = {"success": False, "message": message}
    if detail is not None:
        body["detail"] = detail
    return JSONResponse(status_code=status_code, content=body)


# ── Pagination helper ──────────────────────────────────────────────────────────

def paginate(
    items: List[Any],
    total: int,
    page: int,
    size: int,
) -> dict:
    """
    Build a pagination metadata dict.

    Parameters
    ----------
    items:  Serialised list of objects for the current page.
    total:  Total number of matching records across all pages.
    page:   Current page number (1-based).
    size:   Page size.
    """
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": math.ceil(total / size) if total > 0 else 0,
        "has_next": page * size < total,
        "has_prev": page > 1,
    }