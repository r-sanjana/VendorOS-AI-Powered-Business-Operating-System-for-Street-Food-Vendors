"""
VendorOS - AI: Sales Prediction
Predicts next-day and next-week revenue using a Random Forest Regressor
trained on day-of-week, month, and rolling-average features.

Usage
-----
>>> predictor = SalesPredictor()
>>> predictor.train(historical_revenues)
>>> prediction = predictor.predict_next_day()
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class SalesPrediction:
    """Revenue prediction result."""

    target_date: date
    predicted_revenue: float
    confidence_interval_low: float
    confidence_interval_high: float
    model_accuracy: float  # R² score


class SalesPredictor:
    """
    Sales revenue predictor using scikit-learn RandomForestRegressor.

    Features
    --------
    - Day of week (0=Mon … 6=Sun)
    - Day of month
    - Month of year
    - 7-day rolling average
    """

    def __init__(self) -> None:
        self._model = None
        self._is_trained = False
        self._training_score: float = 0.0
        try:
            from sklearn.ensemble import RandomForestRegressor
            self._model = RandomForestRegressor(
                n_estimators=100, random_state=42, n_jobs=-1
            )
            self._sklearn_available = True
        except ImportError:
            logger.warning("scikit-learn not available; SalesPredictor will use naive mean")
            self._sklearn_available = False
        self._history: List[Tuple[date, float]] = []

    def train(self, history: List[Tuple[date, float]]) -> float:
        """
        Train the model on ``(date, revenue)`` pairs.

        Returns
        -------
        float
            R² accuracy score (0–1).
        """
        self._history = sorted(history, key=lambda x: x[0])
        if not self._sklearn_available or len(history) < 7:
            self._is_trained = False
            return 0.0

        X, y = self._build_features(self._history)
        self._model.fit(X, y)
        self._training_score = float(self._model.score(X, y))
        self._is_trained = True
        return self._training_score

    def predict_next_day(self) -> Optional[SalesPrediction]:
        """Predict revenue for tomorrow."""
        if not self._history:
            return None
        last_date = self._history[-1][0]
        return self._predict_for_date(last_date + timedelta(days=1))

    def predict_next_week(self) -> List[SalesPrediction]:
        """Predict revenue for the next 7 days."""
        if not self._history:
            return []
        last_date = self._history[-1][0]
        return [
            self._predict_for_date(last_date + timedelta(days=i))
            for i in range(1, 8)
        ]

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _predict_for_date(self, target: date) -> SalesPrediction:
        if not self._is_trained:
            mean_rev = (
                sum(r for _, r in self._history) / len(self._history)
                if self._history else 0.0
            )
            return SalesPrediction(
                target_date=target,
                predicted_revenue=round(mean_rev, 2),
                confidence_interval_low=round(mean_rev * 0.8, 2),
                confidence_interval_high=round(mean_rev * 1.2, 2),
                model_accuracy=0.0,
            )

        rolling_avg = self._rolling_avg(self._history, window=7)
        X_pred = np.array([[
            target.weekday(),
            target.day,
            target.month,
            rolling_avg,
        ]])
        pred = float(self._model.predict(X_pred)[0])
        pred = max(0.0, pred)
        margin = pred * 0.15  # ±15% CI placeholder
        return SalesPrediction(
            target_date=target,
            predicted_revenue=round(pred, 2),
            confidence_interval_low=round(max(0.0, pred - margin), 2),
            confidence_interval_high=round(pred + margin, 2),
            model_accuracy=round(self._training_score, 3),
        )

    @staticmethod
    def _build_features(
        history: List[Tuple[date, float]]
    ) -> Tuple[np.ndarray, np.ndarray]:
        revenues = [r for _, r in history]
        X_rows, y_rows = [], []
        window = 7
        for i, (d, rev) in enumerate(history):
            rolling = (
                sum(revenues[max(0, i - window):i]) / min(i, window)
                if i > 0 else rev
            )
            X_rows.append([d.weekday(), d.day, d.month, rolling])
            y_rows.append(rev)
        return np.array(X_rows), np.array(y_rows)

    @staticmethod
    def _rolling_avg(history: List[Tuple[date, float]], window: int) -> float:
        recent = [r for _, r in history[-window:]]
        return sum(recent) / len(recent) if recent else 0.0