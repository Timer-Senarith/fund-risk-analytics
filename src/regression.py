"""Day 4: six-factor regressions - how much of each fund's return is skill (alpha)?"""
import os
from pathlib import Path
import statsmodels.api as sm

import pandas as pd
import numpy as np
from dotenv import load_dotenv
from sqlalchemy import create_engine
from statsmodels.stats.multitest import multipletests

from metrics import load_returns, load_benchmarks      # reuse your Day 3 function

ROOT = Path(__file__).resolve().parents[1]
pd.set_option("display.width", 200)
pd.set_option("display.max_columns", None)
FACTORS = ["mkt_rf", "smb", "hml", "rmw", "cma", "mom"]


def load_factors(engine):
    """Daily Fama-French factors + RF from Neon, indexed by date."""
    return pd.read_sql("SELECT * FROM fact_factors", engine,
                       parse_dates=["date"], index_col="date")

def run_regression(data, fund):
    """Six-factor regression for one fund."""
    y = data[fund] - data["rf"]                  # fund's return above T-bills
    X = sm.add_constant(data[FACTORS])           # the six ingredients + alpha
    return sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 5})

def bootstrap_alpha(data, fund, n=1000, seed=42):
    """95% range for annual alpha, by resampling days 1,000 times."""
    rng = np.random.default_rng(seed)
    y = (data[fund] - data["rf"]).to_numpy()
    X = sm.add_constant(data[FACTORS]).to_numpy()
    alphas = []
    for _ in range(n):
        idx = rng.integers(0, len(y), len(y))                  # random days, with repeats
        coef = np.linalg.lstsq(X[idx], y[idx], rcond=None)[0]  # quick regression
        alphas.append(coef[0] * 252)                           # alpha per year
    return np.percentile(alphas, [2.5, 97.5])

def all_regressions(data, funds):
    """Run the six-factor regression for every active fund."""
    rows = {}
    for fund in funds:
        m = run_regression(data, fund)
        low, high = bootstrap_alpha(data, fund)
        rows[fund] = {
            "alpha_annual": m.params["const"] * 252,
            "alpha_pvalue": m.pvalues["const"],
            "alpha_low": low,
            "alpha_high": high,
            "r_squared": m.rsquared,
            **{f"beta_{f}": m.params[f] for f in FACTORS},
        }
    return pd.DataFrame.from_dict(rows, orient="index")


if __name__ == "__main__":
    load_dotenv(ROOT / ".env")
    engine = create_engine(os.environ["NEON_URL"])

    returns = load_returns(engine)
    factors = load_factors(engine)
    data = returns.join(factors, how="inner")
    active = list(load_benchmarks(engine))          # the 12 active funds
    results = all_regressions(data, active)
    results["alpha_pvalue_adj"] = multipletests(results["alpha_pvalue"], method="fdr_bh")[1]

    show = results.copy()
    for col in ["alpha_annual", "alpha_low", "alpha_high"]:
        show[col] = show[col].map(lambda x: f"{x:.2%}")
    print(show.round(3).sort_values("alpha_pvalue"))

    results.index.name = "ticker"
    results.reset_index().to_sql("fund_alphas", engine, if_exists="replace", index=False)
    print("Saved fund_alphas to Neon:", len(results), "rows")