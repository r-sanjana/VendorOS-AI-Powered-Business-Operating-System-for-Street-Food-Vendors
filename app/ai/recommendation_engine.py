"""
VendorOS - AI: Recommendation Engine
Generates actionable business recommendations and a Vendor Health Score
based on revenue trends, expense ratios, and stock health.

Usage
-----
>>> engine = RecommendationEngine()
>>> result = engine.analyse(vendor_data)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class VendorHealthScore:
    """
    Composite health score for a vendor (0–100).

    Sub-scores
    ----------
    revenue_score:   Based on revenue growth month-over-month.
    expense_score:   Based on profit margin (lower expense ratio → higher score).
    stock_score:     Based on low-stock item ratio.
    overall:         Weighted average of sub-scores.
    """

    revenue_score: float
    expense_score: float
    stock_score: float
    overall: float
    grade: str  # A / B / C / D / F


@dataclass
class BusinessRecommendation:
    """Single actionable recommendation."""

    category: str       # e.g. "inventory", "pricing", "expense"
    priority: str       # "high" / "medium" / "low"
    title: str
    description: str
    impact: str         # expected business impact


@dataclass
class AnalysisResult:
    """Full output of the recommendation engine."""

    vendor_id: str
    health_score: VendorHealthScore
    recommendations: List[BusinessRecommendation]
    insights: Dict[str, Any] = field(default_factory=dict)


class RecommendationEngine:
    """
    Rule-based + ML recommendation engine for VendorOS.

    Phase 1 uses deterministic rules; the ``_ml_insights`` hook is a
    placeholder for future clustering / association-rule models.
    """

    # Weights for composite health score
    _WEIGHTS = {"revenue": 0.40, "expense": 0.40, "stock": 0.20}

    def analyse(
        self,
        vendor_id: str,
        revenue_current_month: float,
        revenue_prev_month: float,
        total_expenses: float,
        total_revenue: float,
        low_stock_count: int,
        total_stock_items: int,
        top_products: Optional[List[Dict[str, Any]]] = None,
    ) -> AnalysisResult:
        """
        Run the full analysis pipeline and return recommendations.

        Parameters
        ----------
        vendor_id:             Vendor UUID string.
        revenue_current_month: Current month's total revenue.
        revenue_prev_month:    Previous month's total revenue.
        total_expenses:        Current month's total expenses.
        total_revenue:         Current month's total revenue (used for margin calc).
        low_stock_count:       Number of items below reorder level.
        total_stock_items:     Total number of inventory items.
        top_products:          Optional list from ``SalesRepository.top_products``.
        """
        health = self._compute_health_score(
            revenue_current_month, revenue_prev_month,
            total_expenses, total_revenue,
            low_stock_count, total_stock_items,
        )
        recommendations = self._generate_recommendations(
            revenue_current_month, revenue_prev_month,
            total_expenses, total_revenue,
            low_stock_count, top_products or [],
        )
        insights = self._ml_insights(top_products or [])

        return AnalysisResult(
            vendor_id=vendor_id,
            health_score=health,
            recommendations=recommendations,
            insights=insights,
        )

    # ── Health score ───────────────────────────────────────────────────────────

    def _compute_health_score(
        self,
        rev_curr: float,
        rev_prev: float,
        expenses: float,
        revenue: float,
        low_stock: int,
        total_stock: int,
    ) -> VendorHealthScore:
        # Revenue growth score (0–100)
        if rev_prev > 0:
            growth = (rev_curr - rev_prev) / rev_prev
            rev_score = min(100.0, max(0.0, 50.0 + growth * 250))
        else:
            rev_score = 50.0 if rev_curr > 0 else 0.0

        # Expense / margin score (0–100)
        if revenue > 0:
            profit_margin = (revenue - expenses) / revenue
            exp_score = min(100.0, max(0.0, profit_margin * 100 * 2))
        else:
            exp_score = 0.0

        # Stock health score (0–100)
        if total_stock > 0:
            healthy_ratio = (total_stock - low_stock) / total_stock
            stock_score = healthy_ratio * 100
        else:
            stock_score = 100.0

        overall = (
            rev_score * self._WEIGHTS["revenue"]
            + exp_score * self._WEIGHTS["expense"]
            + stock_score * self._WEIGHTS["stock"]
        )

        grade = self._grade(overall)
        return VendorHealthScore(
            revenue_score=round(rev_score, 1),
            expense_score=round(exp_score, 1),
            stock_score=round(stock_score, 1),
            overall=round(overall, 1),
            grade=grade,
        )

    @staticmethod
    def _grade(score: float) -> str:
        if score >= 85:
            return "A"
        if score >= 70:
            return "B"
        if score >= 55:
            return "C"
        if score >= 40:
            return "D"
        return "F"

    # ── Recommendations ────────────────────────────────────────────────────────

    def _generate_recommendations(
        self,
        rev_curr: float,
        rev_prev: float,
        expenses: float,
        revenue: float,
        low_stock: int,
        top_products: List[Dict[str, Any]],
    ) -> List[BusinessRecommendation]:
        recs: List[BusinessRecommendation] = []

        # ── Revenue trending down ─────────────────────────────────────────────
        if rev_prev > 0 and rev_curr < rev_prev * 0.9:
            recs.append(BusinessRecommendation(
                category="revenue",
                priority="high",
                title="Revenue decline detected",
                description=(
                    f"Revenue dropped by "
                    f"{((rev_prev - rev_curr) / rev_prev * 100):.1f}% "
                    "compared to last month. Consider promotions or new menu items."
                ),
                impact="Restore previous revenue levels within 4–6 weeks",
            ))

        # ── High expense ratio ────────────────────────────────────────────────
        if revenue > 0:
            expense_ratio = expenses / revenue
            if expense_ratio > 0.75:
                recs.append(BusinessRecommendation(
                    category="expense",
                    priority="high",
                    title="Expense ratio critical",
                    description=(
                        f"Expenses are {expense_ratio * 100:.1f}% of revenue. "
                        "Review raw material costs and consider bulk purchasing."
                    ),
                    impact="Reduce cost ratio by 5–10% through supplier negotiation",
                ))
            elif expense_ratio > 0.60:
                recs.append(BusinessRecommendation(
                    category="expense",
                    priority="medium",
                    title="Expenses above target",
                    description=(
                        "Expense ratio exceeds 60%. Identify the top cost category "
                        "and set a monthly budget."
                    ),
                    impact="Improve profit margin by 5%",
                ))

        # ── Low stock ─────────────────────────────────────────────────────────
        if low_stock > 0:
            recs.append(BusinessRecommendation(
                category="inventory",
                priority="high" if low_stock >= 3 else "medium",
                title=f"{low_stock} item(s) below reorder level",
                description=(
                    "Restock soon to avoid stockouts during peak hours. "
                    "Consider setting up automatic reorder alerts."
                ),
                impact="Prevent lost sales due to unavailability",
            ))

        # ── Promote top products ──────────────────────────────────────────────
        if top_products:
            top = top_products[0]
            recs.append(BusinessRecommendation(
                category="pricing",
                priority="low",
                title=f"Bundle offer: '{top['item_name']}'",
                description=(
                    f"Your best-seller '{top['item_name']}' sold "
                    f"{top['total_quantity']} units this month. "
                    "Create a combo deal to increase average order value."
                ),
                impact="Potential 10–15% uplift in average transaction value",
            ))

        return recs

    # ── ML placeholder ────────────────────────────────────────────────────────

    def _ml_insights(
        self, top_products: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Placeholder for future ML-based association rules / clustering.
        Currently returns basic descriptive stats derived from top products.
        """
        if not top_products:
            return {}

        total_revenue = sum(
            float(p.get("total_revenue", 0)) for p in top_products
        )
        return {
            "product_concentration": {
                "top_item": top_products[0]["item_name"] if top_products else None,
                "top_item_revenue_share": (
                    round(
                        float(top_products[0].get("total_revenue", 0))
                        / total_revenue * 100,
                        1,
                    )
                    if total_revenue > 0 else 0.0
                ),
            },
            "model_version": "rule_based_v1",
            "next_upgrade": "association_rules_v2",
        }