"""Day 5: does alpha persist, and does the answer depend on the model?"""
import os
from pathlib import Path

import pandas as pd
import statsmodels.api as sm
from dotenv import load_dotenv
from sqlalchemy import create_engine

from metrics import load_returns, load_benchmarks
from regression import load_factors, FACTORS

ROOT = Path(__file__).resolve().parents[1]
pd.set_option("display.width", 200)
pd.set_option("display.max_columns", None)
SPLIT_DATE = "2020-12-31"
THREE_FACTORS = ["mkt_rf", "smb", "hml"]


def alpha(data, fund, factors):
    """Annual alpha for one fund, over whatever dates are in `data`."""
    y = data[fund] - data["rf"]                       # what we're explaining
    X = sm.add_constant(data[factors])                # what we explain it with (+ alpha)
    return sm.OLS(y, X).fit().params["const"] * 252   # alpha per year


if __name__ == "__main__":
    load_dotenv(ROOT / ".env")
    engine = create_engine(os.environ["NEON_URL"])

    # Load the data and split it in half
    data = load_returns(engine).join(load_factors(engine), how="inner")
    funds = list(load_benchmarks(engine))
    first = data[data.index <= SPLIT_DATE]      # 2015-2020
    second = data[data.index > SPLIT_DATE]      # 2021-Sep 2026

    # Alpha for each fund: each half, plus the full period with 6 and 3 factors
    table = pd.DataFrame({
        "alpha_2015_2020": [alpha(first, f, FACTORS) for f in funds],
        "alpha_2021_2026": [alpha(second, f, FACTORS) for f in funds],
        "alpha_6_factor": [alpha(data, f, FACTORS) for f in funds],
        "alpha_3_factor": [alpha(data, f, THREE_FACTORS) for f in funds],
    }, index=funds)

    print((table * 100).round(2).sort_values("alpha_2015_2020", ascending=False))

    # Persistence: were the first-half winners also second-half winners?
    persist = table["alpha_2015_2020"].corr(table["alpha_2021_2026"], method="spearman")
    print("\nPersistence (first half vs second half):", round(persist, 2))

    top_before = table["alpha_2015_2020"].rank(ascending=False) <= 6
    top_after = table["alpha_2021_2026"].rank(ascending=False) <= 6
    print("Top-6 funds that stayed in the top 6:", (top_before & top_after).sum(), "of 6")

    # Robustness: does a simpler model rank the funds the same way?
    robust = table["alpha_6_factor"].corr(table["alpha_3_factor"], method="spearman")
    print("Robustness (6-factor vs 3-factor ranking):", round(robust, 2))

    # Save to Neon
    table.index.name = "ticker"
    table.reset_index().to_sql("fund_persistence", engine, if_exists="replace", index=False)
    print("Saved fund_persistence to Neon")