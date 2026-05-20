"""
Laedt OHLCV-Daten fuer alle Portfolio-Titel von Yahoo Finance, speichert
sie unter data/raw/, baut ein Wide-Format Close-Panel unter
data/interim/close_panel.parquet und fuehrt anschliessend Validierungs-
checks aus.

Aufruf:
    python scripts/download_data.py
"""
import pandas as pd

from portfolio_oracle.config import load_config, PROJECT_ROOT
from portfolio_oracle.data.download import download_all_tickers, build_close_panel
from portfolio_oracle.data.validation import validate_panel
from portfolio_oracle.utils.logging import get_logger
from portfolio_oracle.utils.seeds import set_global_seed


def main() -> None:
    set_global_seed(42)
    logger = get_logger("download_data", PROJECT_ROOT / "logs" / "download.log")

    config = load_config()
    tickers = config["portfolio"]["tickers"]
    start = config["period"]["start"]
    end_inclusive = config["period"]["end"]
    # yfinance: end ist exklusiv, daher +1 Tag
    end_exclusive = (pd.Timestamp(end_inclusive) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    raw_dir = PROJECT_ROOT / config["paths"]["data_raw"]
    interim_dir = PROJECT_ROOT / config["paths"]["data_interim"]
    interim_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starte Download fuer {len(tickers)} Ticker: {tickers}")
    logger.info(f"Zeitraum: {start} bis {end_inclusive} (yfinance-end: {end_exclusive})")

    data = download_all_tickers(tickers, start, end_exclusive, raw_dir)
    closes = build_close_panel(data)

    panel_path = interim_dir / "close_panel.parquet"
    closes.to_parquet(panel_path)
    logger.info(f"Close-Panel gespeichert: {panel_path}")

    logger.info("Starte Validierung")
    reports = validate_panel(closes, data)

    n_warnings = sum(1 for r in reports if not r.is_clean())
    if n_warnings > 0:
        logger.warning(f"{n_warnings} Ticker mit Auffaelligkeiten — bitte Log pruefen")
    else:
        logger.info("Alle Ticker sauber")


if __name__ == "__main__":
    main()
