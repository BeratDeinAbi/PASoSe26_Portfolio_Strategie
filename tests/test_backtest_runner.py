import pandas as pd

from portfolio_oracle.backtest.runner import run_backtest
from portfolio_oracle.backtest.state import BacktestState, Order
from portfolio_oracle.backtest.strategy import NoOpStrategy, Strategy


def make_prices() -> pd.DataFrame:
    """Drei Monate, zwei Ticker, einfache lineare Preise."""
    dates = pd.bdate_range("2020-01-01", "2020-03-31")
    df = pd.DataFrame(
        {
            "AAA": [100.0 + i * 0.5 for i in range(len(dates))],
            "BBB": [50.0 + i * 0.25 for i in range(len(dates))],
        },
        index=dates,
    )
    df.index.name = "date"
    return df


def make_config(budget=750.0, fee=1.0, initial=0.0) -> dict:
    return {
        "backtest": {
            "monthly_budget_usd": budget,
            "transaction_fee_usd": fee,
            "initial_capital_usd": initial,
        }
    }


def test_noop_strategy_accumulates_cash():
    prices = make_prices()
    config = make_config()
    result = run_backtest(NoOpStrategy(), prices, config)

    # Drei Monate * 750 USD = 2250 USD, keine Trades
    assert result.equity.iloc[-1] == 2250.0
    assert len(result.trades) == 0
    assert result.positions["cash"].iloc[-1] == 2250.0


class BuyOnceStrategy(Strategy):
    name = "buy_once"

    def __init__(self):
        self.fired = False

    def decide(self, state: BacktestState) -> list[Order]:
        if not self.fired and state.cash >= 501:
            self.fired = True
            return [Order(ticker="AAA", direction="buy", dollar_amount=500.0)]
        return []


def test_buy_order_executes_with_fee():
    prices = make_prices()
    config = make_config(budget=750.0, fee=1.0)
    result = run_backtest(BuyOnceStrategy(), prices, config)

    assert len(result.trades) == 1
    trade = result.trades.iloc[0]
    assert trade["direction"] == "buy"
    assert trade["ticker"] == "AAA"
    assert trade["dollar_amount"] == 500.0
    assert trade["fee"] == 1.0
    assert abs(trade["shares"] - 5.0) < 1e-9


class BuyTooMuchStrategy(Strategy):
    name = "buy_too_much"

    def decide(self, state):
        return [Order(ticker="AAA", direction="buy", dollar_amount=1_000_000.0)]


def test_insufficient_cash_skips_order():
    prices = make_prices()
    config = make_config(budget=750.0, fee=1.0)
    result = run_backtest(BuyTooMuchStrategy(), prices, config)

    assert len(result.trades) == 0
    assert result.equity.iloc[-1] == 2250.0


def test_equity_equals_cash_plus_holdings_value():
    prices = make_prices()
    config = make_config()
    result = run_backtest(BuyOnceStrategy(), prices, config)

    last_date = prices.index[-1]
    final_cash = result.positions["cash"].iloc[-1]
    final_shares_aaa = result.positions["AAA"].iloc[-1]
    final_shares_bbb = result.positions["BBB"].iloc[-1]
    final_price_aaa = prices.loc[last_date, "AAA"]
    final_price_bbb = prices.loc[last_date, "BBB"]

    expected_equity = (
        final_cash
        + final_shares_aaa * final_price_aaa
        + final_shares_bbb * final_price_bbb
    )
    assert abs(result.equity.iloc[-1] - expected_equity) < 1e-6
