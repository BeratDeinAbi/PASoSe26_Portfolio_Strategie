"""Oracle-Strategie: ex-post-optimale Handelsstrategie als MILP."""
from dataclasses import dataclass

import cvxpy as cp
import numpy as np
import pandas as pd

from portfolio_oracle.backtest.budget import first_trading_day_of_each_month
from portfolio_oracle.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class OracleSolution:
    status: str
    final_wealth: float
    solve_time_s: float
    solver: str
    buys: pd.DataFrame
    sells: pd.DataFrame
    decision_days: pd.DatetimeIndex


def _pick_milp_solver() -> str:
    """Waehlt einen installierten MILP-faehigen Solver."""
    available = cp.installed_solvers()
    for candidate in ("HIGHS", "SCIPY", "CBC", "GLPK_MI"):
        if candidate in available:
            return candidate
    raise RuntimeError(f"Kein MILP-Solver verfuegbar. Installiert: {available}")


def solve_oracle(
    prices: pd.DataFrame,
    config: dict,
    time_limit_s: float = 300.0,
) -> OracleSolution:
    """
    Loest die ex-post-optimale Handelsstrategie als MILP.

    Annahmen:
    - Handel nur am ersten Handelstag jedes Monats (Entscheidungstage).
    - Fixe Transaktionsgebuehr pro Order ueber Binaervariablen.
    - Keine Leerverkaeufe, kein Hebel, fraktionale Aktien erlaubt.
    - Zielfunktion: Endvermoegen am letzten Tag des Zeitraums.

    prices: DataFrame, Index = Datum, Spalten = Ticker, Werte = bereinigte
            Schlusskurse in USD.
    """
    tickers = list(prices.columns)
    n = len(tickers)
    dates = prices.index

    budget = float(config["backtest"]["monthly_budget_usd"])
    fee = float(config["backtest"]["transaction_fee_usd"])
    initial = float(config["backtest"]["initial_capital_usd"])

    decision_days = first_trading_day_of_each_month(dates)
    d_count = len(decision_days)

    price_dec = prices.loc[decision_days].to_numpy()
    price_final = prices.iloc[-1].to_numpy()

    total_budget = initial + budget * d_count
    peak_growth = float((prices.max() / prices.iloc[0]).max())
    big_m = total_budget * max(peak_growth, 1.0) * 2.0

    b = cp.Variable((d_count, n), nonneg=True)
    s = cp.Variable((d_count, n), nonneg=True)
    yb = cp.Variable((d_count, n), boolean=True)
    ys = cp.Variable((d_count, n), boolean=True)
    h = cp.Variable((d_count, n), nonneg=True)
    c = cp.Variable(d_count, nonneg=True)

    constraints = []
    for d in range(d_count):
        inflow = budget + (initial if d == 0 else 0.0)
        prev_h = h[d - 1] if d > 0 else np.zeros(n)
        prev_c = c[d - 1] if d > 0 else 0.0
        inv_price = 1.0 / price_dec[d]

        constraints.append(
            h[d] == prev_h + cp.multiply(b[d], inv_price) - cp.multiply(s[d], inv_price)
        )
        constraints.append(
            c[d] == prev_c + inflow + cp.sum(s[d]) - cp.sum(b[d]) - fee * cp.sum(yb[d] + ys[d])
        )
        constraints.append(b[d] <= big_m * yb[d])
        constraints.append(s[d] <= big_m * ys[d])
        constraints.append(s[d] <= cp.multiply(price_dec[d], prev_h))

    final_wealth = c[d_count - 1] + h[d_count - 1] @ price_final
    problem = cp.Problem(cp.Maximize(final_wealth), constraints)

    solver = _pick_milp_solver()
    logger.info(
        f"Oracle-MILP: {d_count} Entscheidungstage, {n} Titel, "
        f"{2 * d_count * n} Binaervariablen, Solver={solver}, big_m={big_m:.0f}"
    )

    solve_kwargs = {"solver": getattr(cp, solver), "verbose": False}
    try:
        problem.solve(time_limit=time_limit_s, **solve_kwargs)
    except TypeError:
        # Solver akzeptiert kein time_limit-Argument
        problem.solve(**solve_kwargs)

    has_solution = b.value is not None
    buys = pd.DataFrame(
        b.value if has_solution else np.zeros((d_count, n)),
        index=decision_days, columns=tickers,
    )
    sells = pd.DataFrame(
        s.value if has_solution else np.zeros((d_count, n)),
        index=decision_days, columns=tickers,
    )

    try:
        solve_time = float(problem.solver_stats.solve_time)
    except (AttributeError, TypeError):
        solve_time = float("nan")

    return OracleSolution(
        status=problem.status,
        final_wealth=float(problem.value) if problem.value is not None else float("nan"),
        solve_time_s=solve_time,
        solver=solver,
        buys=buys,
        sells=sells,
        decision_days=decision_days,
    )
