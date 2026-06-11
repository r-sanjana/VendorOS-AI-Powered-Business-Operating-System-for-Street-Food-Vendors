"""
VendorOS - Tests: AI Module
Unit tests for DemandForecaster, SalesPredictor, and RecommendationEngine.
No database required — pure unit tests.
"""

from datetime import date, timedelta
from typing import List, Tuple

import pytest

from app.ai.demand_forecast import DemandForecaster, DemandForecast
from app.ai.recommendation_engine import RecommendationEngine
from app.ai.sales_prediction import SalesPredictor, SalesPrediction


# ── Helpers ───────────────────────────────────────────────────────────────────

def _daily_history(days: int = 30, base_qty: float = 50.0) -> List[Tuple[date, float]]:
    """Generate synthetic daily quantity history."""
    today = date.today()
    return [
        (today - timedelta(days=days - i), base_qty + (i % 7) * 2.0)
        for i in range(days)
    ]


def _revenue_history(days: int = 30, base: float = 2000.0) -> List[Tuple[date, float]]:
    """Generate synthetic daily revenue history."""
    today = date.today()
    return [
        (today - timedelta(days=days - i), base + (i % 5) * 100.0)
        for i in range(days)
    ]


# ── DemandForecaster ──────────────────────────────────────────────────────────

class TestDemandForecaster:

    def test_returns_correct_number_of_forecasts(self) -> None:
        forecaster = DemandForecaster()
        history = _daily_history(30)
        results = forecaster.forecast(history, item_name="Rice", days_ahead=7)
        assert len(results) == 7

    def test_forecast_dates_are_sequential(self) -> None:
        forecaster = DemandForecaster()
        history = _daily_history(30)
        results = forecaster.forecast(history, item_name="Oil", days_ahead=5)
        for i in range(1, len(results)):
            delta = results[i].forecast_date - results[i - 1].forecast_date
            assert delta.days == 1

    def test_forecast_quantities_non_negative(self) -> None:
        forecaster = DemandForecaster()
        history = _daily_history(30)
        results = forecaster.forecast(history, item_name="Chicken", days_ahead=7)
        for r in results:
            assert r.predicted_quantity >= 0.0

    def test_forecast_confidence_in_range(self) -> None:
        forecaster = DemandForecaster()
        history = _daily_history(30)
        results = forecaster.forecast(history, item_name="Spices", days_ahead=7)
        for r in results:
            assert 0.0 <= r.confidence <= 1.0

    def test_empty_history_returns_empty(self) -> None:
        forecaster = DemandForecaster()
        results = forecaster.forecast([], item_name="Nothing", days_ahead=7)
        assert results == []

    def test_item_name_preserved(self) -> None:
        forecaster = DemandForecaster()
        history = _daily_history(10)
        results = forecaster.forecast(history, item_name="Vegetables", days_ahead=3)
        for r in results:
            assert r.item_name == "Vegetables"

    def test_naive_fallback_with_small_history(self) -> None:
        """With only 2 data points, naive mean is used (no sklearn)."""
        forecaster = DemandForecaster()
        history = _daily_history(2)
        results = forecaster.forecast(history, item_name="Rice", days_ahead=3)
        assert len(results) == 3
        # Naive confidence is 0.5
        for r in results:
            assert r.confidence == 0.5


# ── SalesPredictor ────────────────────────────────────────────────────────────

class TestSalesPredictor:

    def test_train_returns_accuracy_score(self) -> None:
        predictor = SalesPredictor()
        history = _revenue_history(30)
        score = predictor.train(history)
        assert 0.0 <= score <= 1.0

    def test_predict_next_day_returns_result(self) -> None:
        predictor = SalesPredictor()
        history = _revenue_history(30)
        predictor.train(history)
        result = predictor.predict_next_day()
        assert result is not None
        assert isinstance(result, SalesPrediction)
        assert result.predicted_revenue >= 0.0

    def test_predict_next_week_returns_7_items(self) -> None:
        predictor = SalesPredictor()
        history = _revenue_history(30)
        predictor.train(history)
        results = predictor.predict_next_week()
        assert len(results) == 7

    def test_ci_low_lte_predicted_lte_ci_high(self) -> None:
        predictor = SalesPredictor()
        history = _revenue_history(30)
        predictor.train(history)
        for pred in predictor.predict_next_week():
            assert pred.confidence_interval_low <= pred.predicted_revenue
            assert pred.predicted_revenue <= pred.confidence_interval_high

    def test_predict_without_history_returns_none(self) -> None:
        predictor = SalesPredictor()
        result = predictor.predict_next_day()
        assert result is None

    def test_predict_next_week_dates_sequential(self) -> None:
        predictor = SalesPredictor()
        history = _revenue_history(30)
        predictor.train(history)
        results = predictor.predict_next_week()
        for i in range(1, len(results)):
            delta = results[i].target_date - results[i - 1].target_date
            assert delta.days == 1

    def test_insufficient_history_uses_naive_fallback(self) -> None:
        """Less than 7 data points → naive mean prediction."""
        predictor = SalesPredictor()
        history = _revenue_history(4)
        score = predictor.train(history)
        assert score == 0.0
        # Still should give a prediction via naive path
        result = predictor.predict_next_day()
        assert result is not None


# ── RecommendationEngine ──────────────────────────────────────────────────────

class TestRecommendationEngine:

    def _base_analyse(self, **overrides):
        defaults = dict(
            vendor_id="vendor-uuid-001",
            revenue_current_month=50000.0,
            revenue_prev_month=45000.0,
            total_expenses=20000.0,
            total_revenue=50000.0,
            low_stock_count=0,
            total_stock_items=20,
            top_products=[
                {"item_name": "Masala Dosa", "total_quantity": 300, "total_revenue": 18000.0},
                {"item_name": "Filter Coffee", "total_quantity": 200, "total_revenue": 4000.0},
            ],
        )
        defaults.update(overrides)
        engine = RecommendationEngine()
        return engine.analyse(**defaults)

    def test_health_score_in_range(self) -> None:
        result = self._base_analyse()
        assert 0.0 <= result.health_score.overall <= 100.0

    def test_grade_is_letter(self) -> None:
        result = self._base_analyse()
        assert result.health_score.grade in ("A", "B", "C", "D", "F")

    def test_good_business_gets_high_score(self) -> None:
        """Healthy margins + growing revenue + full stock → high score."""
        result = self._base_analyse(
            revenue_current_month=60000.0,
            revenue_prev_month=50000.0,
            total_expenses=15000.0,   # 25% expense ratio → excellent margin
            total_revenue=60000.0,
            low_stock_count=0,
            total_stock_items=20,
        )
        assert result.health_score.overall >= 70.0

    def test_critical_expense_ratio_triggers_high_priority_rec(self) -> None:
        """Expense ratio > 75% should produce a high-priority expense recommendation."""
        result = self._base_analyse(
            total_expenses=40000.0,   # 80% of revenue
            total_revenue=50000.0,
        )
        high_expense_recs = [
            r for r in result.recommendations
            if r.category == "expense" and r.priority == "high"
        ]
        assert len(high_expense_recs) >= 1

    def test_low_stock_triggers_inventory_recommendation(self) -> None:
        result = self._base_analyse(low_stock_count=4, total_stock_items=20)
        inventory_recs = [
            r for r in result.recommendations if r.category == "inventory"
        ]
        assert len(inventory_recs) >= 1
        assert inventory_recs[0].priority == "high"

    def test_revenue_decline_triggers_recommendation(self) -> None:
        result = self._base_analyse(
            revenue_current_month=30000.0,
            revenue_prev_month=50000.0,   # 40% decline
        )
        revenue_recs = [
            r for r in result.recommendations if r.category == "revenue"
        ]
        assert len(revenue_recs) >= 1
        assert revenue_recs[0].priority == "high"

    def test_insights_contain_top_item(self) -> None:
        result = self._base_analyse()
        assert result.insights["product_concentration"]["top_item"] == "Masala Dosa"

    def test_empty_top_products_handled(self) -> None:
        result = self._base_analyse(top_products=[])
        assert result.insights == {}

    def test_zero_revenue_handled_gracefully(self) -> None:
        """No division-by-zero when revenue is 0."""
        result = self._base_analyse(
            revenue_current_month=0.0,
            revenue_prev_month=0.0,
            total_expenses=0.0,
            total_revenue=0.0,
        )
        assert result.health_score.overall >= 0.0

    def test_recommendations_have_required_fields(self) -> None:
        result = self._base_analyse(low_stock_count=2, total_stock_items=10)
        for rec in result.recommendations:
            assert rec.category
            assert rec.priority in ("high", "medium", "low")
            assert rec.title
            assert rec.description
            assert rec.impact