import pandas as pd

from portfolio_oracle.strategies.oracle import solve_oracle


def make_config(budget=100.0, fee=1.0, initial=0.0):
    return {
        "backtest": {
            "monthly_budget_usd": budget,
            "transaction_fee_usd": fee,
            "initial_capital_usd": initial,
        }
    }


def test_single_asset_doubling():
    # 1 Titel, 2 Monate, Preis 10 -> 20.
    # Optimal: Monat 1 maximal kaufen, Monat 2 halten.
    # Endwert ca. 298 (100 Cash aus Monat 2 + 9.9 Aktien * 20).
    dates = pd.DatetimeIndex(["2020-01-01", "2020-02-01"])
    prices = pd.DataFrame({"AAA": [10.0, 20.0]}, index=dates)
    sol = solve_oracle(prices, make_config(budget=100.0, fee=1.0))

    assert sol.status in ("optimal", "optimal_inaccurate")
    assert abs(sol.final_wealth - 298.0) < 1.0


def test_constant_price_holds_cash():
    # Konstanter Preis -> kein Trade lohnt sich.
    # Optimal: nicht handeln, Endwert = 200 (zwei Monate Budget).
    dates = pd.DatetimeIndex(["2020-01-01", "2020-02-01"])
    prices = pd.DataFrame({"AAA": [10.0, 10.0]}, index=dates)
    sol = solve_oracle(prices, make_config(budget=100.0, fee=1.0))

    assert sol.status in ("optimal", "optimal_inaccurate")
    assert abs(sol.final_wealth - 200.0) < 1.0
