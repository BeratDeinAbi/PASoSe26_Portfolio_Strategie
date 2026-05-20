from pathlib import Path
import time
import pandas as pd
import yfinance as yf

from portfolio_oracle.utils.logging import get_logger

logger = get_logger(__name__)


def download_ticker(ticker: str, start: str, end: str, max_retries: int = 3) -> pd.DataFrame:
    """
    Laedt OHLCV-Daten fuer einen Ticker von Yahoo Finance.

    Verwendet auto_adjust=True. Dadurch enthaelt die Spalte 'Close' bereits
    den um Splits und Dividenden bereinigten Kurs. Diese Bereinigung ist
    essenziell, da die spaetere Oracle-Strategie und alle Backtests sonst
    durch Splits systematisch verfaelscht waeren.
    """
    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            df = yf.download(
                ticker,
                start=start,
                end=end,
                auto_adjust=True,
                progress=False,
                threads=False,
            )
            if df.empty:
                raise ValueError(f"Leerer DataFrame fuer {ticker}")

            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # Tz-naive, nur Datum (keine Uhrzeit). Yahoo liefert fuer
            # US-Daily-Daten ohnehin tz-naive Timestamps, wir normalisieren
            # defensiv, falls sich das aendert.
            idx = pd.to_datetime(df.index)
            if idx.tz is not None:
                idx = idx.tz_localize(None)
            df.index = idx.normalize()
            df.index.name = "date"

            logger.info(
                f"{ticker}: {len(df)} Tage von {df.index.min().date()} bis {df.index.max().date()}"
            )
            return df

        except Exception as e:
            last_err = e
            logger.warning(f"{ticker} Versuch {attempt}/{max_retries} fehlgeschlagen: {e}")
            if attempt < max_retries:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"Download fuer {ticker} fehlgeschlagen: {last_err}")


def download_all_tickers(
    tickers: list[str], start: str, end: str, output_dir: Path
) -> dict[str, pd.DataFrame]:
    """
    Laedt OHLCV fuer alle Ticker. Speichert jeden Ticker als
    output_dir/<ticker>.parquet. Gibt {ticker: DataFrame} zurueck.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    data: dict[str, pd.DataFrame] = {}

    for ticker in tickers:
        df = download_ticker(ticker, start, end)
        out_path = output_dir / f"{ticker}.parquet"
        df.to_parquet(out_path)
        logger.info(f"{ticker}: gespeichert unter {out_path}")
        data[ticker] = df

    return data


def build_close_panel(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Baut aus den OHLCV-DataFrames ein Wide-Format-Panel mit Datum als
    Index und Tickern als Spalten, das nur die bereinigten Close-Kurse
    enthaelt.
    """
    closes = pd.DataFrame({ticker: df["Close"] for ticker, df in data.items()})
    closes.index.name = "date"
    closes = closes.sort_index()
    return closes
