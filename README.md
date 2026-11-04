# Fund Performance & Risk Analytics

**Question:** Did actively managed US equity funds earn their fees from 2015 to 2026, once returns are adjusted for risk and factor exposure, and does past outperformance persist?

> **Work in progress.** The data pipeline is being built; analysis, dashboard and findings will follow.

---

## Why this question

Active funds charge far more than index funds. For example, Fidelity Contrafund's expense ratio is about 0.74% a year, while the Fidelity 500 Index fund charges about 0.015%. This project tests whether that extra cost has paid off for investors, and whether any outperformance came from manager skill or from style exposure an investor could buy cheaply.

## Approach

1. **Data pipeline:** download daily prices for 18 funds (12 active, 6 passive benchmarks), Fama-French factors and the risk-free rate; check quality; load into a PostgreSQL star schema.
2. **Risk and return:** total return, CAGR, volatility, maximum drawdown, Sharpe ratio and information ratio for every fund.
3. **Skill vs style:** Fama-French six-factor regressions to estimate each fund's alpha, with bootstrap confidence intervals.
4. **Persistence:** test whether funds with high alpha in one period keep it in the next.
5. **Communication:** a Power BI dashboard and a one-page analyst memo.

## Fund universe

Defined in [`config/funds.csv`](config/funds.csv).

| Group | Funds |
| --- | --- |
| Fidelity (active) | FCNTX, FMAGX, FBGRX, FEQIX, FLPSX |
| Wellington-managed (active) | VWELX, VWNDX, VDIGX |
| Other active managers | AGTHX, TRBCX, DODGX, PRBLX |
| Passive benchmarks | SPY, FXAIX, IWF, IWD, IWR, AOR |

Each active fund is compared with the passive benchmark that matches its style (growth → IWF, value → IWD, mid-cap → IWR, balanced → AOR, broad large-cap → SPY).

## Data sources

| Source | Data | Status |
| --- | --- | --- |
| Yahoo Finance (`yfinance`) | Dividend- and split-adjusted daily prices, fund names, expense ratios | ✅ Done |
| Kenneth French Data Library | Fama-French 5 factors + momentum | ⏳ In progress |
| FRED | 3-month Treasury bill (risk-free rate) | ⏳ In progress |

All returns use **adjusted prices** (total return), so dividends and capital-gain distributions are counted as reinvested.

## Project structure

```
fund-risk-analytics/
├── config/funds.csv        # fund list: names, categories, benchmarks, fees
├── src/extract.py          # downloads raw data into data/raw/
├── notebooks/              # exploration (01_explore.ipynb)
├── sql/                    # database schema and checks
├── tests/                  # unit tests
├── dashboard/              # Power BI files and screenshots
├── memo/                   # analyst memo
└── requirements.txt
```

## How to run

```bash
git clone https://github.com/Timer-Senarith/fund-risk-analytics.git
cd fund-risk-analytics
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python src/extract.py            # downloads prices into data/raw/prices.csv
```

## Roadmap

- [x] Project setup and fund universe
- [x] Fund price extraction
- [ ] Factor and risk-free rate extraction
- [ ] Data-quality checks and PostgreSQL (Neon) star schema
- [ ] Risk and return metrics
- [ ] Factor regressions and bootstrap confidence intervals
- [ ] Persistence and robustness tests
- [ ] Power BI dashboard and analyst memo

## Tools

Python (pandas, NumPy, yfinance, statsmodels, pytest) · PostgreSQL (Neon) · Snowflake · Power BI · Git
