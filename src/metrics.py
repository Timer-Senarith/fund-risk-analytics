"""Day 3: risk metrics for every fund, read from Neon."""
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

ROOT = Path(__file__).resolve().parents[1]

# Step 1. get the returns table (dates down, funds across)
def load_returns(engine):
    """Daily returns from Neon, one column per fund."""
    prices = pd.read_sql(
        "SELECT ticker, date, daily_return FROM fact_daily_prices",
        engine, parse_dates=["date"],
    )
    returns = prices.pivot(index="date", columns="ticker", values="daily_return")   # pivot: rows = date, columns = ticker, values = daily_return
    return returns.dropna(how="all")   # drop the first day (no return yet)

def load_rf(engine, dates):
    """Daily risk-free rate (FRED T-bill), lined up with the fund dates."""
    rates = pd.read_sql("SELECT date, rf_daily FROM fact_rates", engine,
                        parse_dates=["date"], index_col="date")
    return rates["rf_daily"].reindex(dates).ffill()

# Step 2 + 3. build each fund's $1 line, then read 4 numbers off it
def basic_metrics(returns, rf):
    """Total return, CAGR, volatility and max drawdown for every fund."""
    wealth = (1 + returns).cumprod()                    # growth of 1 dollar, 1 column per fund
    years = len(returns) /252                           # trading days to years

    total_return = wealth.iloc[-1] - 1                   # 1. last value of $1, minus 1
    cagr =(1 + total_return) ** (1 / years) - 1
    volatility = returns.std() * 252 ** 0.5  # 3. daily → annual
    drawdown = wealth / wealth.cummax() - 1  # 4. fall from running peak
    excess = returns.sub(rf, axis=0)                          # daily return above T-bills
    sharpe = excess.mean() / excess.std() * 252 ** 0.5        # annualized Sharpe

    return pd.DataFrame({
        "total_return": total_return,
        "cagr": cagr,
        "volatility": volatility,
        "max_drawdown": drawdown.min(),
        "max_drawdown_date": drawdown.idxmin(),
        "sharpe": sharpe,
    })


if __name__ == "__main__":
    load_dotenv(ROOT / ".env")
    engine = create_engine(os.environ["NEON_URL"])

    returns = load_returns(engine)
    rf = load_rf(engine, returns.index)
    metrics = basic_metrics(returns, rf)

    show = metrics.copy()
    for col in ["total_return", "cagr", "volatility", "max_drawdown"]:
        show[col] = show[col].map(lambda x: f"{x:.1%}")
    show["sharpe"] = show["sharpe"].round(2)
    print(show.sort_values("sharpe", ascending=False))

