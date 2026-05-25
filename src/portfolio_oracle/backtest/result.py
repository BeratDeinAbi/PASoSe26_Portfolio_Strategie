"""Backtest-Ergebnis-Klasse und Persistenz auf Festplatte."""
import json
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd


@dataclass
class BacktestResult:
    """Vollstaendiges Ergebnis eines Backtest-Laufs."""
    strategy_name: str
    config: dict
    equity: pd.Series           # Index: date, Wert: Gesamtportfolio in USD
    positions: pd.DataFrame     # Index: date, Spalten: "cash" + Ticker-Shares
    trades: pd.DataFrame        # date, ticker, direction, shares, dollar_amount, fee, price
    metadata: dict = field(default_factory=dict)

    def summary(self) -> dict:
        if len(self.equity) == 0:
            return {
                "strategy_name": self.strategy_name,
                "final_equity": 0.0,
                "n_trades": 0,
                "total_fees": 0.0,
                "date_start": None,
                "date_end": None,
            }
        return {
            "strategy_name": self.strategy_name,
            "final_equity": float(self.equity.iloc[-1]),
            "n_trades": int(len(self.trades)),
            "total_fees": float(self.trades["fee"].sum()) if len(self.trades) else 0.0,
            "date_start": str(self.equity.index.min().date()),
            "date_end": str(self.equity.index.max().date()),
        }


def save_result(result: BacktestResult, results_dir: Path) -> Path:
    """
    Speichert ein BacktestResult unter results_dir/<strategy_name>/.
    Erzeugt vier Dateien: equity.parquet, positions.parquet,
    trades.parquet, metadata.json.
    """
    target_dir = results_dir / result.strategy_name
    target_dir.mkdir(parents=True, exist_ok=True)

    result.equity.to_frame("equity").to_parquet(target_dir / "equity.parquet")
    result.positions.to_parquet(target_dir / "positions.parquet")
    result.trades.to_parquet(target_dir / "trades.parquet")

    meta = {
        "strategy_name": result.strategy_name,
        "config": result.config,
        "summary": result.summary(),
        **result.metadata,
    }
    with open(target_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, default=str)

    return target_dir


def load_result(strategy_dir: Path) -> BacktestResult:
    """Laedt ein BacktestResult aus einem Strategie-Verzeichnis."""
    equity = pd.read_parquet(strategy_dir / "equity.parquet")["equity"]
    positions = pd.read_parquet(strategy_dir / "positions.parquet")
    trades = pd.read_parquet(strategy_dir / "trades.parquet")

    with open(strategy_dir / "metadata.json", "r", encoding="utf-8") as f:
        meta = json.load(f)

    return BacktestResult(
        strategy_name=meta["strategy_name"],
        config=meta.get("config", {}),
        equity=equity,
        positions=positions,
        trades=trades,
        metadata={k: v for k, v in meta.items() if k not in ("strategy_name", "config")},
    )
