"""Copy the star schema into Snowflake and create an annual-returns view."""
import os
from pathlib import Path

import snowflake.connector as sc
from dotenv import load_dotenv
from snowflake.connector.pandas_tools import write_pandas

from load import build_tables   # same 5 tables as Neon

ROOT = Path(__file__).resolve().parents[1]

SETUP = [
    "CREATE WAREHOUSE IF NOT EXISTS COMPUTE_WH WITH WAREHOUSE_SIZE='XSMALL' AUTO_SUSPEND=60 AUTO_RESUME=TRUE",
    "USE WAREHOUSE COMPUTE_WH",
    "CREATE DATABASE IF NOT EXISTS FUND_RISK",
    "CREATE SCHEMA IF NOT EXISTS FUND_RISK.ANALYTICS",
    "USE SCHEMA FUND_RISK.ANALYTICS",
]

KEYS = [
    "ALTER TABLE DIM_FUND ADD PRIMARY KEY (TICKER)",
    "ALTER TABLE DIM_DATE ADD PRIMARY KEY (DATE)",
    "ALTER TABLE FACT_DAILY_PRICES ADD PRIMARY KEY (TICKER, DATE)",
    "ALTER TABLE FACT_FACTORS ADD PRIMARY KEY (DATE)",
    "ALTER TABLE FACT_RATES ADD PRIMARY KEY (DATE)",
    "ALTER TABLE FACT_DAILY_PRICES ADD FOREIGN KEY (TICKER) REFERENCES DIM_FUND (TICKER)",
    "ALTER TABLE FACT_DAILY_PRICES ADD FOREIGN KEY (DATE) REFERENCES DIM_DATE (DATE)",
    "ALTER TABLE FACT_FACTORS ADD FOREIGN KEY (DATE) REFERENCES DIM_DATE (DATE)",
    "ALTER TABLE FACT_RATES ADD FOREIGN KEY (DATE) REFERENCES DIM_DATE (DATE)",
]

ANNUAL_RETURNS_VIEW = """
CREATE OR REPLACE VIEW V_ANNUAL_RETURNS AS
WITH year_end AS (
    SELECT p.TICKER, d.YEAR, MAX_BY(p.ADJ_CLOSE, p.DATE) AS YEAR_END_PRICE
    FROM FACT_DAILY_PRICES p
    JOIN DIM_DATE d ON p.DATE = d.DATE
    GROUP BY p.TICKER, d.YEAR
)
SELECT y.TICKER, f.NAME, f.ACTIVE_PASSIVE, y.YEAR,
       y.YEAR_END_PRICE / LAG(y.YEAR_END_PRICE) OVER (PARTITION BY y.TICKER ORDER BY y.YEAR) - 1
           AS ANNUAL_RETURN
FROM year_end y
JOIN DIM_FUND f ON y.TICKER = f.TICKER
"""


if __name__ == "__main__":
    load_dotenv(ROOT / ".env")
    tables = build_tables()

    with sc.connect(account=os.environ["SNOWFLAKE_ACCOUNT"],
                    user=os.environ["SNOWFLAKE_USER"],
                    private_key_file=os.environ["SNOWFLAKE_PRIVATE_KEY_PATH"],
                    role="ACCOUNTADMIN") as conn:
        cur = conn.cursor()
        for statement in SETUP:
            cur.execute(statement)

        # Start clean: drop fact tables first, then dimensions
        for name in reversed(list(tables)):
            cur.execute(f"DROP TABLE IF EXISTS {name.upper()} CASCADE")

        # Upload each table (dates as real DATE values)
        for name, df in tables.items():
            df = df.copy()
            if "date" in df.columns:
                df["date"] = df["date"].dt.date
            ok, _, nrows, _ = write_pandas(conn, df, name.upper(),
                                           auto_create_table=True, quote_identifiers=False)
            print(f"Loaded {name.upper()}: {nrows} rows")

        for statement in KEYS:
            cur.execute(statement)
        print("Added primary and foreign keys")

        cur.execute(ANNUAL_RETURNS_VIEW)
        print("Created view V_ANNUAL_RETURNS")

        # Cross-check against quality.py's Morningstar table
        rows = cur.execute("""
            SELECT TICKER, YEAR, ROUND(ANNUAL_RETURN * 100, 2)
            FROM V_ANNUAL_RETURNS
            WHERE TICKER IN ('FCNTX', 'SPY', 'VWELX') AND YEAR BETWEEN 2022 AND 2024
            ORDER BY TICKER, YEAR
        """).fetchall()
        for ticker, year, ret in rows:
            print(f"  {ticker} {year}: {ret}%")
