from app.schemas.base import VendorOSSchema, PaginatedResponse
from app.schemas.user_schema import (
    UserRegisterRequest, UserLoginRequest,
    UserResponse, TokenResponse, AuthResponse,
)
from app.schemas.vendor_schema import (
    VendorCreateRequest, VendorUpdateRequest, VendorResponse,
)
from app.schemas.inventory_schema import (
    InventoryItemCreateRequest, InventoryItemUpdateRequest,
    InventoryItemResponse, StockMovementCreateRequest, StockMovementResponse,
    LowStockAlert,
)
from app.schemas.sales_schema import (
    SaleCreateRequest, SaleResponse, SaleItemResponse,
    RevenueSummary, TopProduct,
)
from app.schemas.expense_schema import (
    ExpenseCreateRequest, ExpenseUpdateRequest,
    ExpenseResponse, ExpenseAnalytics,
)
from app.schemas.dashboard_schema import (
    DashboardSummary, RevenueBreakdown, ExpenseBreakdown,
    ProfitSummary, TopProductsResponse,
)