"""Download raw data for the fund risk analytics project."""
import warnings

import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore", message=".*inplace keyword.*")

START_DATE = "2015-01-01"

def download_prices(tickers, start=START_DATE):
        """Download adjusted daily closing prices for each ticker."""
        today = pd.Timestamp.today().strftime("%Y-%m-%d")  # NEW: e.g. "2026-11-09"
        frames = []
        for t in tickers:
            prices = yf.Ticker(t).history(start=start, end=today, auto_adjust=True)["Close"]  # NEW: end=today
            prices.index = prices.index.tz_localize(None)
            df = pd.DataFrame({"date": prices.index, "ticker": t, "adj_close": prices.values})
            frames.append(df)
            print(f"{t}: {len(df)} rows")
        return pd.concat(frames, ignore_index=True)


if __name__ == "__main__":
    funds = pd.read_csv("config/funds.csv")
    prices = download_prices(funds["ticker"])
    prices.to_csv("data/raw/prices.csv", index=False)
    print("Saved", len(prices), "rows")