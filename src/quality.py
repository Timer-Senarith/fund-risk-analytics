"""Data-quality checks on the raw files before loading to the database."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
CONFIG = ROOT / "config" / "funds.csv"
FACTOR_COLS = ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "Mom"]

results = []   # each check adds (status, message)


def check(passed, message, level="FAIL"):
    """Record one check result: PASS, or FAIL/WARN if it didn't pass."""
    status = "PASS" if passed else level
    results.append((status, message))
    print(f"[{status}] {message}")


def check_prices(prices):
    prices = prices.sort_values(["ticker", "date"])

    # 1. No missing prices
    n_missing = prices["adj_close"].isna().sum()
    check(n_missing == 0, f"Prices: {n_missing} missing values")

    # 2. No duplicate ticker + date rows
    n_dupes = prices.duplicated(subset=["ticker", "date"]).sum()
    check(n_dupes == 0, f"Prices: {n_dupes} duplicate ticker-date rows")

    # 3. Every fund has the same number of rows
    counts = prices.groupby("ticker").size()
    check(counts.nunique() == 1, f"Prices: row counts per fund {counts.min()}–{counts.max()}")

    # 4. Every fund starts in early January 2015
    latest_start = prices.groupby("ticker")["date"].min().max()
    check(latest_start <= pd.Timestamp("2015-01-10"),
          f"Prices: latest fund start date {latest_start.date()}")

    # 5. No zero or negative prices
    n_bad = (prices["adj_close"] <= 0).sum()
    check(n_bad == 0, f"Prices: {n_bad} prices at or below zero")

    # 6. Extreme daily moves (could be real, so WARN not FAIL)
    prices["ret"] = prices.groupby("ticker")["adj_close"].pct_change()
    big = prices[prices["ret"].abs() > 0.15]
    check(len(big) == 0, f"Prices: {len(big)} daily moves bigger than 15%", level="WARN")
    for row in big.itertuples():
        print(f"         {row.ticker} {row.date.date()} {row.ret:+.1%}")

    # 7. No long gaps between trading days
    max_gap = prices.groupby("ticker")["date"].diff().dt.days.max()
    check(max_gap <= 5, f"Prices: largest gap between trading days is {max_gap:.0f} days", level="WARN")


def check_factors(factors, prices):
    # 8. No missing factor values
    n_missing = factors.isna().sum().sum()
    check(n_missing == 0, f"Factors: {n_missing} missing values")

    # 9. Values are decimals, not percent (a daily move of 20%+ would be a unit error)
    max_abs = factors[FACTOR_COLS].abs().max().max()
    check(max_abs < 0.2, f"Factors: largest daily value {max_abs:.4f} (should be < 0.2)")

    # 10. Risk-free rate never negative
    n_neg = (factors["RF"] < 0).sum()
    check(n_neg == 0, f"Factors: {n_neg} negative RF values")

    # 11. Publication lag is normal (under ~2 months)
    lag = (prices["date"].max() - factors["date"].max()).days
    check(lag <= 60, f"Factors: end {factors['date'].max().date()}, {lag} days behind prices", level="WARN")


def check_rates(rates):
    # 12. No missing rates
    n_missing = rates["rf_daily"].isna().sum()
    check(n_missing == 0, f"Rates: {n_missing} missing values")

    # 13. Daily rate in a sensible range (0% to ~12.6% a year)
    in_range = rates["rf_daily"].between(-0.00001, 0.0005).all()
    check(in_range, f"Rates: daily rate range {rates['rf_daily'].min():.6f}–{rates['rf_daily'].max():.6f}")


def check_funds(funds, prices):
    # 14. Tickers are unique
    check(funds["ticker"].is_unique, "Funds: tickers are unique")

    # 15. Fees are decimals between 0% and 2%
    check(funds["expense_ratio"].between(0, 0.02).all(),
          f"Funds: fees range {funds['expense_ratio'].min():.6f}–{funds['expense_ratio'].max():.4f}")

    # 16. Every active fund's benchmark is one of the passive funds
    passive = set(funds.loc[funds["active_passive"] == "passive", "ticker"])
    active = funds[funds["active_passive"] == "active"]
    bad = active.loc[~active["benchmark"].isin(passive), "ticker"].tolist()
    check(len(bad) == 0, f"Funds: active funds with an unknown benchmark: {bad}")

    # 17. Same tickers in funds.csv and prices.csv
    missing = set(funds["ticker"]) ^ set(prices["ticker"])
    check(len(missing) == 0, f"Funds: tickers not in both files: {sorted(missing)}")


def annual_returns(prices, tickers=("FCNTX", "VWELX", "SPY"), years=(2022, 2023, 2024)):
    """Calendar-year total returns, to compare by hand with Morningstar."""
    p = prices[prices["ticker"].isin(tickers)].sort_values("date")
    year_end = p.groupby([p["date"].dt.year, "ticker"])["adj_close"].last().unstack()
    return (year_end.pct_change().loc[list(years)] * 100).round(2)


if __name__ == "__main__":
    prices = pd.read_csv(RAW / "prices.csv", parse_dates=["date"])
    factors = pd.read_csv(RAW / "factors.csv", parse_dates=["date"])
    rates = pd.read_csv(RAW / "rates.csv", parse_dates=["date"])
    funds = pd.read_csv(CONFIG)

    check_prices(prices)
    check_factors(factors, prices)
    check_rates(rates)
    check_funds(funds, prices)

    n_fail = sum(1 for s, _ in results if s == "FAIL")
    n_warn = sum(1 for s, _ in results if s == "WARN")
    print(f"\n{len(results)} checks: {n_fail} failed, {n_warn} warnings")

    print("\nCalendar-year returns (%) — compare with Morningstar:")
    print(annual_returns(prices))