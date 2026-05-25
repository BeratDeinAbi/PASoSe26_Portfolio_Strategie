import pandas as pd

from portfolio_oracle.backtest.budget import first_trading_day_of_each_month


def test_returns_first_of_each_month():
    dates = pd.DatetimeIndex([
        "2020-01-02", "2020-01-03", "2020-01-06",
        "2020-02-03", "2020-02-04",
        "2020-03-02",
    ])
    result = first_trading_day_of_each_month(dates)
    expected = pd.DatetimeIndex(["2020-01-02", "2020-02-03", "2020-03-02"])
    assert list(result) == list(expected)


def test_handles_unsorted_input():
    dates = pd.DatetimeIndex([
        "2020-02-03", "2020-01-06", "2020-01-02", "2020-02-04",
    ])
    result = first_trading_day_of_each_month(dates)
    expected = pd.DatetimeIndex(["2020-01-02", "2020-02-03"])
    assert list(result) == list(expected)


def test_single_day_returns_that_day():
    dates = pd.DatetimeIndex(["2020-01-15"])
    result = first_trading_day_of_each_month(dates)
    assert len(result) == 1
    assert result[0] == pd.Timestamp("2020-01-15")
