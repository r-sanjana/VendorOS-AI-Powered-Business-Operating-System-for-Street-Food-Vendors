"""
VendorOS - Utility: Date / Time Helpers
Centralised date-range builders used by analytics services.
"""

from datetime import date, timedelta
from typing import Tuple


def today() -> date:
    """Return today's date (UTC-equivalent for server-side use)."""
    return date.today()


def current_month_range() -> Tuple[date, date]:
    """Return (first_day_of_month, today) for the current calendar month."""
    t = today()
    return t.replace(day=1), t


def previous_month_range() -> Tuple[date, date]:
    """Return (first_day, last_day) for the previous calendar month."""
    t = today()
    first_this_month = t.replace(day=1)
    last_prev = first_this_month - timedelta(days=1)
    first_prev = last_prev.replace(day=1)
    return first_prev, last_prev


def current_week_range() -> Tuple[date, date]:
    """Return (Monday, today) for the current ISO week."""
    t = today()
    start = t - timedelta(days=t.weekday())  # Monday
    return start, t


def last_n_days(n: int) -> Tuple[date, date]:
    """Return (today - n days, today)."""
    t = today()
    return t - timedelta(days=n), t


def date_range_days(start: date, end: date) -> int:
    """Return the number of calendar days between *start* and *end* inclusive."""
    return (end - start).days + 1