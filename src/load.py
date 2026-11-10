"""Load the raw files into Neon (PostgreSQL) as a star schema."""
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import Date, create_engine, text

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"

KEYS = [
    "ALTER TABLE dim_fund ADD PRIMARY KEY (ticker)",
    "ALTER TABLE dim_date ADD PRIMARY KEY (date)",
    "ALTER TABLE fact_daily_prices ADD PRIMARY KEY (ticker, date)",
    "ALTER TABLE fact_factors ADD PRIMARY KEY (date)",
    "ALTER TABLE fact_rates ADD PRIMARY KEY (date)",
    "ALTER TABLE fact_daily_prices ADD FOREIGN KEY (ticker) REFERENCES dim_fund (ticker)",
    "ALTER TABLE fact_daily_prices ADD FOREIGN KEY (date) REFERENCES dim_date (date)",
    "ALTER TABLE fact_factors ADD FOREIGN KEY (date) REFERENCES dim_date (date)",
    "ALTER TABLE fact_rates ADD FOREIGN KEY (date) REFERENCES dim_date (date)",
]


def build_tables():
    """Turn the raw CSVs into the five star-schema tables."""
    funds = pd.read_csv(ROOT / "config" / "funds.csv")
    prices = pd.read_csv(RAW / "prices.csv", parse_dates=["date"])
    factors = pd.read_csv(RAW / "factors.csv", parse_dates=["date"])
    rates = pd.read_csv(RAW / "rates.csv", parse_dates=["date"])

    # dim_date: every date that appears in any fact table
    all_dates = pd.concat([prices["date"], factors["date"], rates["date"]]).drop_duplicates().sort_values()
    dim_date = pd.DataFrame({"date": all_dates})
    dim_date["year"] = dim_date["date"].dt.year
    dim_date["quarter"] = dim_date["date"].dt.quarter
    dim_date["month"] = dim_date["date"].dt.month
    dim_date["weekday"] = dim_date["date"].dt.day_name()

    # fact_daily_prices: add each fund's daily return
    prices = prices.sort_values(["ticker", "date"])
    prices["daily_return"] = prices.groupby("ticker")["adj_close"].pct_change()

    # SQL-friendly column names (no dashes or capitals)
    factors = factors.rename(columns={"Mkt-RF": "mkt_rf", "SMB": "smb", "HML": "hml",
                                      "RMW": "rmw", "CMA": "cma", "RF": "rf", "Mom": "mom"})
    rates = rates.rename(columns={"DTB3": "dtb3"})

    return {
        "dim_fund": funds,
        "dim_date": dim_date,
        "fact_daily_prices": prices,
        "fact_factors": factors,
        "fact_rates": rates,
    }


if __name__ == "__main__":
    load_dotenv(ROOT / ".env")
    engine = create_engine(os.environ["NEON_URL"])
    tables = build_tables()

    # Start clean: drop old tables (CASCADE also removes their keys)
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS " + ", ".join(tables) + " CASCADE"))

    # Load each table
    for name, df in tables.items():
        dtype = {"date": Date()} if "date" in df.columns else None
        df.to_sql(name, engine, index=False, dtype=dtype, method="multi", chunksize=2000)
        print(f"Loaded {name}: {len(df)} rows")

    # Add primary and foreign keys
    with engine.begin() as conn:
        for statement in KEYS:
            conn.execute(text(statement))
    print("Added primary and foreign keys")

    # Check the row counts in Neon match
    with engine.connect() as conn:
        for name in tables:
            n = conn.execute(text(f"SELECT COUNT(*) FROM {name}")).scalar()
            print(f"  {name}: {n} rows in Neon")