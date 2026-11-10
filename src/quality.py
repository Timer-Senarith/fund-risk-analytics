"""Data-quality checks on the raw files before loading to the database."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"

results = []   # each check adds (status, message)


def check(passed, message, level="FAIL"):
    """Record one check result: PASS, or FAIL/WARN if it didn't pass."""
    status = "PASS" if passed else level
    results.append((status, message))
    print(f"[{status}] {message}")


def check_prices(prices):
    # 1. No missing prices
    n_missing = prices["adj_close"].isna().sum()
    check(n_missing == 0, f"Prices: {n_missing} missing values")

    # 2. No duplicate ticker + date rows
    n_dupes = prices.duplicated(subset=["ticker", "date"]).sum()
    check(n_dupes == 0, f"Prices: {n_dupes} duplicate ticker-date rows")

    # 3. Every fund has the same number of rows
    counts = prices.groupby("ticker").size()
    check(counts.nunique() == 1, f"Prices: row counts per fund {counts.min()}–{counts.max()}")


if __name__ == "__main__":
    prices = pd.read_csv(RAW / "prices.csv", parse_dates=["date"])
    check_prices(prices)

    n_fail = sum(1 for s, _ in results if s == "FAIL")
    n_warn = sum(1 for s, _ in results if s == "WARN")
    print(f"\n{len(results)} checks: {n_fail} failed, {n_warn} warnings")