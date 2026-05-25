"""Datenklassen fuer Backtest-Zustand und Orders."""
from dataclasses import dataclass
from typing import Literal

import pandas as pd


@dataclass(frozen=True)
class Order:
    """Eine einzelne Order, die das Backtest-Framework ausfuehrt."""
    ticker: str
    direction: Literal["buy", "sell"]
    dollar_amount: float  # Immer positiv. Richtung in `direction`.


@dataclass
class BacktestState:
    """Zustand des Portfolios zu einem Zeitpunkt waehrend des Backtests."""
    date: pd.Timestamp
    prices: pd.DataFrame  # Historische Kurse bis einschliesslich `date`
    cash: float  # USD
    holdings: dict[str, float]  # Ticker -> fraktionale Aktienanzahl
