"""
VendorOS - AI Routes
Exposes ML-powered endpoints: demand forecasting, sales prediction,
vendor health score and business recommendations.
"""

from datetime import date, timedelta
from typing import Any, Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.demand_forecast import DemandForecaster
from app.ai.recommendation_engine import AnalysisResult, RecommendationEngine
from app.ai.sales_prediction import SalesPredictor, SalesPrediction
from app.core.dependencies import get_current_user_id, get_db
from app.core.exceptions import NotFoundError
from app.repositories.expense_repository import ExpenseRepository
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.sales_repository import SalesRepository
from app.repositories.vendor_repository import VendorRepository

router = APIRouter(prefix="/ai", tags=["AI & Insights"])


# ── Demand Forecast ────────────────────────────────────────────────────────────

@router.get(
    "/demand-forecast",
    summary="Predict item demand for the next N days",
    response_model=List[Dict[str, Any]],
)
async def demand_forecast(
    vendor_id: UUID = Query(...),
    item_name: str = Query(..., description="Exact item name as recorded in sales"),
    days_ahead: int = Query(default=7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
) -> List[Dict[str, Any]]:
    """
    Forecast demand for a specific item using historical daily sales quantities.
    Requires at least 3 days of sales history for meaningful predictions.
    """
    sales_repo = SalesRepository(db)
    end_date = date.today()
    start_date = end_date - timedelta(days=90)

    top = await sales_repo.top_products(vendor_id, start_date, end_date, top_n=100)
    # Build daily quantity history for the requested item
    item_row = next((r for r in top if r["item_name"] == item_name), None)

    # Use a simple history: treat the last 30 days as uniform daily split
    if item_row:
        total_qty = float(item_row["total_quantity"])
        # Approximate daily history (30 data points)
        history = [
            (end_date - timedelta(days=30 - i), total_qty / 30)
            for i in range(30)
        ]
    else:
        history = []

    forecaster = DemandForecaster()
    forecasts = forecaster.forecast(history, item_name=item_name, days_ahead=days_ahead)
    return [
        {
            "item_name": f.item_name,
            "forecast_date": f.forecast_date.isoformat(),
            "predicted_quantity": f.predicted_quantity,
            "confidence": f.confidence,
        }
        for f in forecasts
    ]


# ── Sales Prediction ───────────────────────────────────────────────────────────

@router.get(
    "/sales-prediction",
    summary="Predict next-day and next-week revenue",
    response_model=Dict[str, Any],
)
async def sales_prediction(
    vendor_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
) -> Dict[str, Any]:
    """
    Train a RandomForest model on 90 days of daily revenue history and
    return predictions for tomorrow and the next 7 days.
    """
    sales_repo = SalesRepository(db)
    today = date.today()

    # Build daily revenue history
    history: List[tuple] = []
    for i in range(89, -1, -1):
        d = today - timedelta(days=i)
        rev = await sales_repo.daily_revenue(vendor_id, d)
        if float(rev) > 0:
            history.append((d, float(rev)))

    predictor = SalesPredictor()
    accuracy = predictor.train(history)

    next_day = predictor.predict_next_day()
    next_week = predictor.predict_next_week()

    def _fmt(p: SalesPrediction) -> Dict[str, Any]:
        return {
            "target_date": p.target_date.isoformat(),
            "predicted_revenue": p.predicted_revenue,
            "confidence_interval_low": p.confidence_interval_low,
            "confidence_interval_high": p.confidence_interval_high,
            "model_accuracy": p.model_accuracy,
        }

    return {
        "vendor_id": str(vendor_id),
        "training_data_points": len(history),
        "model_accuracy": round(accuracy, 3),
        "next_day": _fmt(next_day) if next_day else None,
        "next_week": [_fmt(p) for p in next_week],
    }


# ── Vendor Health Score + Recommendations ─────────────────────────────────────

@router.get(
    "/insights",
    response_model=Dict[str, Any],
    summary="Vendor health score and business recommendations",
)
async def vendor_insights(
    vendor_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
) -> Dict[str, Any]:
    """
    Analyse the vendor's current-month performance and return:
    - A composite health score (0–100, graded A–F)
    - Actionable recommendations (inventory, pricing, expenses)
    - Product concentration insights
    """
    vendor_repo = VendorRepository(db)
    sales_repo = SalesRepository(db)
    expense_repo = ExpenseRepository(db)
    inventory_repo = InventoryRepository(db)

    vendor = await vendor_repo.get_by_id(vendor_id)
    if vendor is None:
        raise NotFoundError("Vendor", vendor_id)

    today = date.today()
    month_start = today.replace(day=1)

    # Previous month boundaries
    if today.month == 1:
        prev_month_start = date(today.year - 1, 12, 1)
        prev_month_end = date(today.year, 1, 1) - timedelta(days=1)
    else:
        prev_month_start = date(today.year, today.month - 1, 1)
        prev_month_end = month_start - timedelta(days=1)

    rev_curr = float(
        await sales_repo.revenue_for_period(vendor_id, month_start, today)
    )
    rev_prev = float(
        await sales_repo.revenue_for_period(vendor_id, prev_month_start, prev_month_end)
    )
    expenses = float(
        await expense_repo.total_for_period(vendor_id, month_start, today)
    )
    top_products = await sales_repo.top_products(vendor_id, month_start, today, top_n=5)
    low_stock_items = await inventory_repo.get_low_stock_items(vendor_id)
    all_items, total_stock = await inventory_repo.get_by_vendor(vendor_id, 0, 9999)

    engine = RecommendationEngine()
    result: AnalysisResult = engine.analyse(
        vendor_id=str(vendor_id),
        revenue_current_month=rev_curr,
        revenue_prev_month=rev_prev,
        total_expenses=expenses,
        total_revenue=rev_curr,
        low_stock_count=len(low_stock_items),
        total_stock_items=total_stock,
        top_products=top_products,
    )

    return {
        "vendor_id": str(vendor_id),
        "business_name": vendor.business_name,
        "health_score": {
            "overall": result.health_score.overall,
            "grade": result.health_score.grade,
            "revenue_score": result.health_score.revenue_score,
            "expense_score": result.health_score.expense_score,
            "stock_score": result.health_score.stock_score,
        },
        "recommendations": [
            {
                "category": r.category,
                "priority": r.priority,
                "title": r.title,
                "description": r.description,
                "impact": r.impact,
            }
            for r in result.recommendations
        ],
        "insights": result.insights,
    }