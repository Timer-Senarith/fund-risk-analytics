"""Download raw data for the fund risk analytics project."""
import warnings
from pathlib import Path

import pandas as pd
import yfinance as yf
from pandas_datareader import data as pdr

warnings.filterwarnings("ignore", message=".*inplace keyword.*")

ROOT = Path(__file__).resolve().parents[1]
START_DATE = "2015-01-01"


def download_prices(tickers, start=START_DATE):
    """Download adjusted daily closing prices for each ticker."""
    today = pd.Timestamp.today().strftime("%Y-%m-%d")
    frames = []
    for t in tickers:
        prices = yf.Ticker(t).history(start=start, end=today, auto_adjust=True)["Close"]
        prices.index = prices.index.tz_localize(None)
        df = pd.DataFrame({"date": prices.index, "ticker": t, "adj_close": prices.values})
        frames.append(df)
        print(f"{t}: {len(df)} rows")
    return pd.concat(frames, ignore_index=True)


def download_factors(start=START_DATE):
    """Download daily Fama-French 5 factors + momentum as decimals."""
    ff5 = pdr.DataReader("F-F_Research_Data_5_Factors_2x3_daily", "famafrench", start=start)[0]
    mom = pdr.DataReader("F-F_Momentum_Factor_daily", "famafrench", start=start)[0]

    factors = (ff5 / 100).join(mom / 100, how="inner")
    factors = factors.reset_index().rename(columns={"Date": "date"})
    factors["date"] = factors["date"].dt.to_timestamp()   # NEW: Period → Timestamp, matches prices
    return factors


if __name__ == "__main__":
    funds = pd.read_csv(ROOT / "config" / "funds.csv")

    prices = download_prices(funds["ticker"])
    prices.to_csv(ROOT / "data" / "raw" / "prices.csv", index=False)
    print("Saved", len(prices), "price rows")

    factors = download_factors()
    factors.to_csv(ROOT / "data" / "raw" / "factors.csv", index=False)
    print("Saved", len(factors), "factor rows, ending", factors["date"].max().date())