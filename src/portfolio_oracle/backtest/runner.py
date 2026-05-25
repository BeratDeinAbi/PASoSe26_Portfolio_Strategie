"""Der eigentliche Backtest-Runner — gemeinsam fuer alle Strategien."""
import pandas as pd

from portfolio_oracle.backtest.budget import first_trading_day_of_each_month
from portfolio_oracle.backtest.result import BacktestResult
from portfolio_oracle.backtest.state import BacktestState, Order
from portfolio_oracle.backtest.strategy import Strategy
from portfolio_oracle.utils.logging import get_logger

logger = get_logger(__name__)


def run_backtest(
    strategy: Strategy,
    prices: pd.DataFrame,
    config: dict,
) -> BacktestResult:
    """
    Fuehrt einen Backtest fuer die gegebene Strategie auf den gegebenen
    Kursdaten unter den Bedingungen in `config` durch.

    Args:
        strategy: Eine Implementierung von Strategy.
        prices: DataFrame, Index = Datum, Spalten = Ticker, Werte =
                bereinigte Schlusskurse in USD.
        config: Backtest-Konfiguration. Erwartet:
                config["backtest"]["monthly_budget_usd"]
                config["backtest"]["transaction_fee_usd"]
                config["backtest"]["initial_capital_usd"]

    Returns:
        BacktestResult mit Equity-Kurve, Positionen, Trade-Log und Metadaten.
    """
    backtest_cfg = config["backtest"]
    monthly_budget = float(backtest_cfg["monthly_budget_usd"])
    fee = float(backtest_cfg["transaction_fee_usd"])
    initial_capital = float(backtest_cfg["initial_capital_usd"])

    tickers = list(prices.columns)
    cash = initial_capital
    holdings: dict[str, float] = {t: 0.0 for t in tickers}

    budget_dates = set(first_trading_day_of_each_month(prices.index))

    equity_records: dict = {}
    positions_records: list[dict] = []
    trade_records: list[dict] = []
    skipped_orders = 0

    for date in prices.index:
        # 1) Monatliches Budget zufuehren am ersten Handelstag des Monats
        if date in budget_dates:
            cash += monthly_budget

        # 2) Strategie um Entscheidung bitten
        state = BacktestState(
            date=date,
            prices=prices.loc[:date],
            cash=cash,
            holdings=dict(holdings),
        )
        orders = strategy.decide(state)

        current_prices = prices.loc[date]

        # 3) Orders ausfuehren
        for order in orders:
            if order.ticker not in tickers:
                logger.warning(f"{date.date()}: Unbekannter Ticker {order.ticker}, uebersprungen")
                skipped_orders += 1
                continue

            price = float(current_prices[order.ticker])
            if pd.isna(price) or price <= 0:
                logger.warning(f"{date.date()}: Ungueltiger Preis fuer {order.ticker}, uebersprungen")
                skipped_orders += 1
                continue

            amount = float(order.dollar_amount)
            if amount <= 0:
                skipped_orders += 1
                continue

            if order.direction == "buy":
                total_cost = amount + fee
                if cash < total_cost:
                    skipped_orders += 1
                    continue
                shares = amount / price
                cash -= total_cost
                holdings[order.ticker] += shares
                trade_records.append({
                    "date": date,
                    "ticker": order.ticker,
                    "direction": "buy",
                    "shares": shares,
                    "dollar_amount": amount,
                    "fee": fee,
                    "price": price,
                })

            elif order.direction == "sell":
                shares_to_sell = amount / price
                if holdings[order.ticker] < shares_to_sell - 1e-9:
                    skipped_orders += 1
                    continue
                holdings[order.ticker] -= shares_to_sell
                cash += amount - fee
                trade_records.append({
                    "date": date,
                    "ticker": order.ticker,
                    "direction": "sell",
                    "shares": shares_to_sell,
                    "dollar_amount": amount,
                    "fee": fee,
                    "price": price,
                })
            else:
                logger.warning(f"{date.date()}: Unbekannte Richtung {order.direction}, uebersprungen")
                skipped_orders += 1

        # 4) Zustand fuer diesen Tag protokollieren
        holdings_value = 0.0
        for t in tickers:
            p = float(current_prices[t])
            if not pd.isna(p):
                holdings_value += holdings[t] * p
        equity = cash + holdings_value
        equity_records[date] = equity
        positions_records.append({
            "date": date,
            "cash": cash,
            **{t: holdings[t] for t in tickers},
        })

    equity_series = pd.Series(equity_records, name="equity")
    equity_series.index.name = "date"

    positions_df = pd.DataFrame(positions_records).set_index("date")

    if trade_records:
        trades_df = pd.DataFrame(trade_records)
    else:
        trades_df = pd.DataFrame(
            columns=["date", "ticker", "direction", "shares", "dollar_amount", "fee", "price"]
        )

    metadata = {
        "n_trading_days": int(len(prices)),
        "n_budget_injections": int(len(budget_dates)),
        "total_budget_injected": float(monthly_budget * len(budget_dates) + initial_capital),
        "skipped_orders": int(skipped_orders),
    }

    final_equity = float(equity_series.iloc[-1]) if len(equity_series) else 0.0
    logger.info(
        f"Backtest {strategy.name}: Endvermoegen {final_equity:.2f} USD, "
        f"{len(trades_df)} Trades, {skipped_orders} uebersprungen"
    )

    return BacktestResult(
        strategy_name=strategy.name,
        config=config,
        equity=equity_series,
        positions=positions_df,
        trades=trades_df,
        metadata=metadata,
    )
