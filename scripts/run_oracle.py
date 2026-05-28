"""
Loest die Oracle-Strategie und meldet Status, Endvermoegen, Solver und
Loesungszeit. Standardmaessig wird zuerst ein kleines Teilfenster geloest
(Tractability-Test). Mit --full wird die gesamte Periode geloest.

Aufruf:
    python scripts/run_oracle.py
    python scripts/run_oracle.py --full
    python scripts/run_oracle.py --assets 3 --months 18
"""
import argparse
import time

import pandas as pd

from portfolio_oracle.config import PROJECT_ROOT, load_config
from portfolio_oracle.data.loader import load_close_panel
from portfolio_oracle.strategies.oracle import solve_oracle
from portfolio_oracle.utils.logging import get_logger


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true", help="Gesamte Periode loesen")
    parser.add_argument("--assets", type=int, default=2, help="Anzahl Titel im Teilfenster")
    parser.add_argument("--months", type=int, default=12, help="Anzahl Monate im Teilfenster")
    args = parser.parse_args()

    logger = get_logger("run_oracle", PROJECT_ROOT / "logs" / "oracle.log")
    config = load_config()
    prices = load_close_panel()

    if not args.full:
        tickers = list(prices.columns)[: args.assets]
        cutoff = prices.index[0] + pd.DateOffset(months=args.months)
        prices = prices.loc[prices.index < cutoff, tickers]
        logger.info(f"Teilfenster: {len(tickers)} Titel, {len(prices)} Handelstage")
    else:
        logger.info(f"Gesamte Periode: {len(prices.columns)} Titel, {len(prices)} Handelstage")

    start = time.time()
    sol = solve_oracle(prices, config)
    elapsed = time.time() - start

    logger.info(f"Status: {sol.status}")
    logger.info(f"Solver: {sol.solver}")
    logger.info(f"Endvermoegen: {sol.final_wealth:.2f} USD")
    logger.info(f"Loesungszeit (Wanduhr): {elapsed:.1f} s")
    n_buys = int((sol.buys.to_numpy() > 1e-6).sum())
    n_sells = int((sol.sells.to_numpy() > 1e-6).sum())
    logger.info(f"Kauforders: {n_buys}, Verkauforders: {n_sells}")


if __name__ == "__main__":
    main()
