"""Hilfsfunktionen fuer die monatliche Budgetzufuehrung."""
import pandas as pd


def first_trading_day_of_each_month(dates: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """
    Liefert den ersten Handelstag jedes Monats im gegebenen Datumsindex.
    Wird verwendet, um den monatlichen Budgetzufluss zu terminieren.
    """
    if not dates.is_monotonic_increasing:
        dates = dates.sort_values()

    first_days = []
    seen: set[tuple[int, int]] = set()
    for d in dates:
        key = (d.year, d.month)
        if key not in seen:
            seen.add(key)
            first_days.append(d)
    return pd.DatetimeIndex(first_days)
