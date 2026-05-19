from portfolio_oracle.config import load_config


def test_config_loads():
    config = load_config()
    assert len(config["portfolio"]["tickers"]) == 8
    assert config["backtest"]["monthly_budget_usd"] == 750.0


def test_seeds_module_importable():
    from portfolio_oracle.utils.seeds import set_global_seed
    set_global_seed(123)
