"""
VendorOS - Main Application Entry Point
========================================
Bootstraps the FastAPI application:
  • CORS middleware
  • Global exception handlers
  • All API routers
  • Database init/dispose lifecycle hooks
  • OpenAPI metadata
"""

import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import VendorOSException
from app.database.connection import dispose_db, init_db
from app.routes.auth import router as auth_router
from app.routes.vendor import router as vendor_router
from app.routes.inventory import router as inventory_router
from app.routes.sales import router as sales_router
from app.routes.expense import router as expense_router
from app.routes.dashboard import router as dashboard_router
from app.routes.ai_routes import router as ai_router
from app.utils.logging import setup_logging

logger = logging.getLogger(__name__)


# ── Lifespan (startup / shutdown) ─────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    FastAPI lifespan context manager.
    Runs startup tasks before ``yield`` and shutdown tasks after.
    """
    setup_logging()
    logger.info("🚀 Starting %s v%s [%s]", settings.APP_NAME, settings.APP_VERSION, settings.ENVIRONMENT)

    # In development, auto-create tables. In production use Alembic migrations.
    if settings.ENVIRONMENT in ("development", "test"):
        await init_db()
        logger.info("✅ Database tables verified / created")

    yield

    logger.info("🛑 Shutting down %s …", settings.APP_NAME)
    await dispose_db()
    logger.info("✅ Database connection pool disposed")


# ── App factory ───────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    """
    Application factory.
    Returns a configured ``FastAPI`` instance.
    """
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "## VendorOS — Street Food Vendor Management Platform\n\n"
            "A production-grade SaaS backend for managing:\n"
            "- 🔐 Authentication & Role-based access\n"
            "- 🏪 Vendor profiles\n"
            "- 📦 Inventory & stock movements\n"
            "- 💰 Sales tracking & revenue analytics\n"
            "- 🧾 Expense management & profit calculation\n"
            "- 📊 Dashboard KPIs\n"
            "- 🤖 AI-powered demand forecasting & recommendations\n"
        ),
        openapi_url="/api/openapi.json",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        lifespan=lifespan,
        debug=settings.DEBUG,
    )

    # ── Middleware ─────────────────────────────────────────────────────────────
    _register_middleware(app)

    # ── Exception handlers ─────────────────────────────────────────────────────
    _register_exception_handlers(app)

    # ── Routers ────────────────────────────────────────────────────────────────
    _register_routers(app)

    return app


# ── Middleware setup ───────────────────────────────────────────────────────────

def _register_middleware(app: FastAPI) -> None:
    """Register all application middleware."""

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request ID / logging middleware (lightweight inline version)
    @app.middleware("http")
    async def log_requests(request: Request, call_next: Any) -> Any:
        logger.debug(
            "→ %s %s  [client=%s]",
            request.method,
            request.url.path,
            request.client.host if request.client else "unknown",
        )
        response = await call_next(request)
        logger.debug(
            "← %s %s  [status=%d]",
            request.method,
            request.url.path,
            response.status_code,
        )
        return response


# ── Exception handlers ────────────────────────────────────────────────────────

def _register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers for consistent error responses."""

    @app.exception_handler(VendorOSException)
    async def vendoros_exception_handler(
        request: Request, exc: VendorOSException
    ) -> JSONResponse:
        """Handle all domain-specific VendorOS exceptions."""
        logger.warning(
            "Domain error [%d] on %s %s: %s",
            exc.status_code, request.method, request.url.path, exc.message,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": exc.message,
                "detail": exc.detail,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handle Pydantic / FastAPI request validation errors with clear messages."""
        errors = []
        for error in exc.errors():
            field = " → ".join(str(loc) for loc in error["loc"])
            errors.append({"field": field, "message": error["msg"]})

        logger.debug(
            "Validation error on %s %s: %s",
            request.method, request.url.path, errors,
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "message": "Request validation failed",
                "errors": errors,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Catch-all for unexpected errors — never expose internal details."""
        logger.exception(
            "Unhandled exception on %s %s", request.method, request.url.path
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "An internal server error occurred. Please try again later.",
            },
        )


# ── Router registration ────────────────────────────────────────────────────────

def _register_routers(app: FastAPI) -> None:
    """Mount all domain routers under the /api/v1 prefix."""

    API_PREFIX = "/api/v1"

    app.include_router(auth_router,      prefix=API_PREFIX)
    app.include_router(vendor_router,    prefix=API_PREFIX)
    app.include_router(inventory_router, prefix=API_PREFIX)
    app.include_router(sales_router,     prefix=API_PREFIX)
    app.include_router(expense_router,   prefix=API_PREFIX)
    app.include_router(dashboard_router, prefix=API_PREFIX)
    app.include_router(ai_router,        prefix=API_PREFIX)

    # ── Health check (no auth required) ───────────────────────────────────────
    @app.get("/health", tags=["Health"], summary="Liveness probe")
    async def health() -> dict:
        """Returns 200 OK. Used by load balancers and container orchestrators."""
        return {
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
        }

    @app.get("/", tags=["Health"], summary="Root redirect")
    async def root() -> dict:
        return {"message": f"Welcome to {settings.APP_NAME} API", "docs": "/api/docs"}


# ── Application instance ──────────────────────────────────────────────────────

app: FastAPI = create_app()


# ── Dev entrypoint ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
    )