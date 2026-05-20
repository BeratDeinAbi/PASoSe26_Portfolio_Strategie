import numpy as np
import pandas as pd

from portfolio_oracle.data.validation import (
    validate_ticker,
    check_trading_day_alignment,
)


def make_df(prices):
    dates = pd.date_range("2020-01-01", periods=len(prices), freq="B")
    return pd.DataFrame(
        {
            "Open": prices,
            "High": prices,
            "Low": prices,
            "Close": prices,
            "Volume": [1000] * len(prices),
        },
        index=pd.DatetimeIndex(dates, name="date"),
    )


def test_clean_ticker_passes():
    df = make_df([100.0, 101.0, 102.0, 101.5])
    report = validate_ticker("TEST", df)
    assert report.is_clean()
    assert report.n_rows == 4


def test_detects_nan_close():
    df = make_df([100.0, np.nan, 102.0])
    report = validate_ticker("TEST", df)
    assert report.n_missing_close == 1
    assert not report.is_clean()


def test_detects_extreme_return():
    # 100 -> 200 entspricht +100%, ueber dem 50%-Threshold
    df = make_df([100.0, 200.0, 200.0])
    report = validate_ticker("TEST", df)
    assert len(report.extreme_returns) == 1


def test_alignment_counts_nans_per_ticker():
    closes = pd.DataFrame(
        {
            "AAA": [100.0, 101.0, np.nan, 103.0],
            "BBB": [50.0, np.nan, 52.0, 53.0],
        }
    )
    nans = check_trading_day_alignment(closes)
    assert nans == {"AAA": 1, "BBB": 1}
