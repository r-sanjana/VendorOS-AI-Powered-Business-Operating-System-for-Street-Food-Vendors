"""
VendorOS - AI: Demand Forecasting
Predicts item demand for the next N days using a linear regression model
trained on historical daily sales quantities.

Usage
-----
>>> forecaster = DemandForecaster()
>>> predictions = forecaster.forecast(history=[(date, qty), ...], days_ahead=7)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, List, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class DemandForecast:
    """Single-item demand forecast result."""

    item_name: str
    forecast_date: date
    predicted_quantity: float
    confidence: float  # 0.0 – 1.0


class DemandForecaster:
    """
    Lightweight demand forecasting using scikit-learn LinearRegression.

    The model is trained on (day_index → quantity) pairs and predicts
    future quantities for ``days_ahead`` future days.
    """

    def __init__(self) -> None:
        try:
            from sklearn.linear_model import LinearRegression
            self._model_cls = LinearRegression
            self._sklearn_available = True
        except ImportError:
            logger.warning("scikit-learn not installed; using naive mean forecast")
            self._sklearn_available = False

    def forecast(
        self,
        history: List[Tuple[date, float]],
        item_name: str = "item",
        days_ahead: int = 7,
    ) -> List[DemandForecast]:
        """
        Forecast demand for the next *days_ahead* days.

        Parameters
        ----------
        history:
            List of ``(date, quantity)`` tuples ordered chronologically.
        item_name:
            Label attached to each forecast result.
        days_ahead:
            Number of future days to predict.

        Returns
        -------
        List[DemandForecast]
        """
        if not history:
            return []

        quantities = [q for _, q in history]

        if self._sklearn_available and len(history) >= 3:
            return self._sklearn_forecast(history, item_name, days_ahead)
        else:
            return self._naive_forecast(quantities, history[-1][0], item_name, days_ahead)

    # ── sklearn path ──────────────────────────────────────────────────────────

    def _sklearn_forecast(
        self,
        history: List[Tuple[date, float]],
        item_name: str,
        days_ahead: int,
    ) -> List[DemandForecast]:
        from sklearn.linear_model import LinearRegression
        from sklearn.preprocessing import StandardScaler

        X = np.array(range(len(history))).reshape(-1, 1)
        y = np.array([q for _, q in history])

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        model = LinearRegression()
        model.fit(X_scaled, y)

        r2 = float(model.score(X_scaled, y))
        confidence = max(0.0, min(1.0, r2))

        last_date = history[-1][0]
        results = []
        for i in range(1, days_ahead + 1):
            future_idx = np.array([[len(history) - 1 + i]])
            future_scaled = scaler.transform(future_idx)
            predicted = float(model.predict(future_scaled)[0])
            predicted = max(0.0, predicted)
            results.append(
                DemandForecast(
                    item_name=item_name,
                    forecast_date=last_date + timedelta(days=i),
                    predicted_quantity=round(predicted, 2),
                    confidence=round(confidence, 3),
                )
            )
        return results

    # ── Naive (mean) fallback ─────────────────────────────────────────────────

    def _naive_forecast(
        self,
        quantities: List[float],
        last_date: date,
        item_name: str,
        days_ahead: int,
    ) -> List[DemandForecast]:
        mean_qty = sum(quantities) / len(quantities)
        return [
            DemandForecast(
                item_name=item_name,
                forecast_date=last_date + timedelta(days=i),
                predicted_quantity=round(mean_qty, 2),
                confidence=0.5,
            )
            for i in range(1, days_ahead + 1)
        ]