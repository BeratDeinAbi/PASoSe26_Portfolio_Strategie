from dataclasses import dataclass, field
import pandas as pd

from portfolio_oracle.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ValidationReport:
    ticker: str
    n_rows: int
    date_start: pd.Timestamp
    date_end: pd.Timestamp
    n_missing_close: int
    n_negative_prices: int
    extreme_returns: list = field(default_factory=list)

    def is_clean(self) -> bool:
        return (
            self.n_missing_close == 0
            and self.n_negative_prices == 0
            and len(self.extreme_returns) == 0
        )

    def summary(self) -> str:
        status = "OK" if self.is_clean() else "WARN"
        return (
            f"[{status}] {self.ticker}: {self.n_rows} Tage, "
            f"{self.date_start.date()} bis {self.date_end.date()}, "
            f"NaN Close: {self.n_missing_close}, "
            f"Neg. Preise: {self.n_negative_prices}, "
            f"Extreme Renditen: {len(self.extreme_returns)}"
        )


def validate_ticker(
    ticker: str, df: pd.DataFrame, extreme_return_threshold: float = 0.5
) -> ValidationReport:
    """
    Prueft einen Ticker-DataFrame auf:
    - Fehlende Close-Werte
    - Negative oder Null-Preise
    - Extreme Tagesrenditen (Standard: > 50%), die auf nicht angepasste
      Splits oder Datenfehler hinweisen koennen.
    """
    n_missing = int(df["Close"].isna().sum())
    n_negative = int((df["Close"] <= 0).sum())

    returns = df["Close"].pct_change().dropna()
    extremes = returns[returns.abs() > extreme_return_threshold]
    extreme_list = [(idx, float(val)) for idx, val in extremes.items()]

    return ValidationReport(
        ticker=ticker,
        n_rows=len(df),
        date_start=df.index.min(),
        date_end=df.index.max(),
        n_missing_close=n_missing,
        n_negative_prices=n_negative,
        extreme_returns=extreme_list,
    )


def check_trading_day_alignment(closes: pd.DataFrame) -> dict[str, int]:
    """
    Zaehlt NaNs pro Ticker im Wide-Format-Panel. NaNs hier deuten auf
    Tage hin, an denen andere Ticker einen Wert haben, dieser aber nicht
    (z. B. spaeterer Boersengang, einzelne Datenluecken).
    """
    return {ticker: int(closes[ticker].isna().sum()) for ticker in closes.columns}


def validate_panel(
    closes: pd.DataFrame, data: dict[str, pd.DataFrame]
) -> list[ValidationReport]:
    """Erzeugt Reports fuer alle Ticker und loggt Alignment-Informationen."""
    reports = [validate_ticker(ticker, df) for ticker, df in data.items()]

    for r in reports:
        logger.info(r.summary())

    alignment = check_trading_day_alignment(closes)
    logger.info(f"NaNs pro Ticker im Close-Panel: {alignment}")
    logger.info(
        f"Panel-Zeitraum: {closes.index.min().date()} bis {closes.index.max().date()}, "
        f"{len(closes)} Handelstage"
    )

    return reports
