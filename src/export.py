"""Day 6: export results from Neon to CSV files for Tableau Public."""
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dashboard" / "data"

# One row per fund: details + scorecard + alpha + persistence
SUMMARY_SQL = """
SELECT f.ticker, f.name, f.firm, f.active_passive, f.category, f.benchmark, f.expense_ratio,
       m.total_return, m.cagr, m.volatility, m.max_drawdown, m.max_drawdown_date, m.sharpe,
       m.beta, m.tracking_error, m.info_ratio,
       a.alpha_annual, a.alpha_low, a.alpha_high, a.alpha_pvalue, a.alpha_pvalue_adj, a.r_squared,
       p.alpha_2015_2020, p.alpha_2021_2026
FROM dim_fund f
JOIN fund_metrics m ON f.ticker = m.ticker
LEFT JOIN fund_alphas a ON f.ticker = a.ticker
LEFT JOIN fund_persistence p ON f.ticker = p.ticker
ORDER BY f.active_passive, m.sharpe DESC
"""

# One row per fund per day: price, for the growth-of-$1 chart
GROWTH_SQL = """
SELECT p.date, p.ticker, f.name, f.active_passive, p.adj_close
FROM fact_daily_prices p
JOIN dim_fund f ON p.ticker = f.ticker
ORDER BY p.ticker, p.date
"""


if __name__ == "__main__":
    load_dotenv(ROOT / ".env")
    engine = create_engine(os.environ["NEON_URL"])
    OUT.mkdir(parents=True, exist_ok=True)

    summary = pd.read_sql(SUMMARY_SQL, engine)
    summary.to_csv(OUT / "fund_summary.csv", index=False)
    print("Saved fund_summary.csv:", len(summary), "rows")

    growth = pd.read_sql(GROWTH_SQL, engine, parse_dates=["date"])
    growth["growth_of_1"] = growth["adj_close"] / growth.groupby("ticker")["adj_close"].transform("first")
    growth.to_csv(OUT / "fund_growth.csv", index=False)
    print("Saved fund_growth.csv:", len(growth), "rows")