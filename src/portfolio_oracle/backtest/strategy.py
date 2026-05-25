"""Abstrakte Basisklasse fuer alle Strategien."""
from abc import ABC, abstractmethod

from portfolio_oracle.backtest.state import BacktestState, Order


class Strategy(ABC):
    """
    Basisklasse fuer alle Handelsstrategien.

    Jede Strategie implementiert `decide`, das fuer einen gegebenen
    Backtest-Zustand eine Liste von Orders zurueckgibt. Der Backtest-Runner
    ruft `decide` einmal pro Handelstag auf — NACHDEM ggf. der monatliche
    Budget-Zufluss verbucht wurde.
    """

    name: str = "abstract"

    @abstractmethod
    def decide(self, state: BacktestState) -> list[Order]:
        raise NotImplementedError


class NoOpStrategy(Strategy):
    """Macht nichts. Nuetzlich zum Testen des Framework-Cashflows."""
    name = "noop"

    def decide(self, state: BacktestState) -> list[Order]:
        return []
