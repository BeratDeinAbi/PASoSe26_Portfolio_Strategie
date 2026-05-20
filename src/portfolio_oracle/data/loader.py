from pathlib import Path
import pandas as pd

from portfolio_oracle.config import load_config, PROJECT_ROOT


def _resolve_raw_dir(raw_dir: Path | None) -> Path:
    if raw_dir is not None:
        return raw_dir
    config = load_config()
    return PROJECT_ROOT / config["paths"]["data_raw"]


def load_ticker(ticker: str, raw_dir: Path | None = None) -> pd.DataFrame:
    raw_dir = _resolve_raw_dir(raw_dir)
    path = raw_dir / f"{ticker}.parquet"
    if not path.exists():
        raise FileNotFoundError(
            f"Cache fehlt: {path}. Bitte scripts/download_data.py ausfuehren."
        )
    return pd.read_parquet(path)


def load_all_tickers(
    tickers: list[str] | None = None, raw_dir: Path | None = None
) -> dict[str, pd.DataFrame]:
    if tickers is None:
        tickers = load_config()["portfolio"]["tickers"]
    raw_dir = _resolve_raw_dir(raw_dir)
    return {ticker: load_ticker(ticker, raw_dir) for ticker in tickers}


def load_close_panel(
    tickers: list[str] | None = None, raw_dir: Path | None = None
) -> pd.DataFrame:
    data = load_all_tickers(tickers, raw_dir)
    closes = pd.DataFrame({ticker: df["Close"] for ticker, df in data.items()})
    closes.index.name = "date"
    return closes.sort_index()
