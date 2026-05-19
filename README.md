# Portfolio Oracle — DS-Projekt

Ex-post-optimale Portfolio-Strategie als Benchmark zur Bewertung
klassischer Handelsindikatoren und Machine-Learning-Modelle.

## Setup

python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"

## Projektstruktur

- src/portfolio_oracle/ — Hauptpaket
- config/config.yaml — Zentrale Parameter
- data/ — Rohdaten (nicht versioniert)
- notebooks/ — Exploration
- tests/ — Unit-Tests
- reports/ — Abbildungen und Bericht

## Konfiguration

Alle Parameter (Tickers, Zeitraum, Budget, Transaktionskosten)
liegen in config/config.yaml.

## Tests

pytest
