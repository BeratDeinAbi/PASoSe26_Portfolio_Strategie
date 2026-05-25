from pathlib import Path

import pandas as pd

from portfolio_oracle.backtest.result import (
    BacktestResult,
    load_result,
    save_result,
)


def make_dummy_result() -> BacktestResult:
    dates = pd.DatetimeIndex(pd.bdate_range("2020-01-01", periods=5).date)
    equity = pd.Series(
        [1000.0, 1010.0, 1005.0, 1020.0, 1030.0],
        index=dates,
        name="equity",
    )
    equity.index.name = "date"
    positions = pd.DataFrame(
        {
            "cash": [1000.0, 500.0, 500.0, 500.0, 500.0],
            "AAA": [0.0, 5.0, 5.0, 5.0, 5.0],
        },
        index=dates,
    )
    positions.index.name = "date"
    trades = pd.DataFrame(
        [
            {
                "date": dates[1],
                "ticker": "AAA",
                "direction": "buy",
                "shares": 5.0,
                "dollar_amount": 500.0,
                "fee": 1.0,
                "price": 100.0,
            }
        ]
    )
    return BacktestResult(
        strategy_name="test_strategy",
        config={"backtest": {"monthly_budget_usd": 750.0}},
        equity=equity,
        positions=positions,
        trades=trades,
        metadata={"foo": "bar"},
    )


def test_save_load_roundtrip(tmp_path: Path):
    original = make_dummy_result()
    save_result(original, tmp_path)

    loaded = load_result(tmp_path / "test_strategy")

    assert loaded.strategy_name == original.strategy_name
    pd.testing.assert_series_equal(
        loaded.equity, original.equity, check_index_type=False
    )
    pd.testing.assert_frame_equal(
        loaded.positions, original.positions, check_index_type=False
    )
    assert len(loaded.trades) == len(original.trades)


def test_summary_returns_expected_keys():
    result = make_dummy_result()
    summary = result.summary()
    assert "strategy_name" in summary
    assert "final_equity" in summary
    assert "n_trades" in summary
    assert summary["final_equity"] == 1030.0
    assert summary["n_trades"] == 1
