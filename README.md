# Fund Performance & Risk Analytics

**Do active fund managers earn their fees?**

This project tests 12 actively managed US mutual funds against low-cost passive benchmarks from 2015 to 2026. It uses a SQL star-schema warehouse, Fama-French factor regressions, and multiple-testing correction, and presents the results in a Tableau Public dashboard.

📊 **Dashboard:** [Fund Performance & Risk Analytics on Tableau Public](https://public.tableau.com/views/Book1_17945886122090/Doactivefundmanagersearntheirfees20152026)

---

## Key findings

| # | Finding | Evidence |
|---|---|---|
| 1 | **Most active funds lost to the market after fees** | 9 of 12 funds have a negative annual alpha, net of fees, under the 6-factor model |
| 2 | **No fund showed skill that can be told apart from luck** | The best fund, FBGRX, has +3.4% alpha (raw p = 0.027), but after the Benjamini–Hochberg FDR correction p = 0.33 |
| 3 | **Past winners don't reliably keep winning** | The rank correlation of alpha between 2015–2020 and 2021–2026 is only 0.40. 10 of 12 funds had negative alpha in the second half |
| 4 | **The results are robust** | Alphas from the 3-factor and 6-factor models have a rank correlation of 0.96 |

**Bottom line:** for most investors, a low-cost index fund is the sensible default. A fund's strong track record on its own is weak evidence that the manager is skilled.

---

## Pipeline

```
 Yahoo Finance        Kenneth French        FRED
 (daily prices)       (6 factors)           (3-month T-bill)
        \                  |                  /
         └──────────► extract.py ◄───────────┘
                          │
                     quality.py      17 automated data checks (FAIL / WARN)
                          │
            ┌─────────────┴─────────────┐
        load.py                  load_snowflake.py
   Neon PostgreSQL               Snowflake mirror and
   (star schema)                 validation view
            │
   metrics.py  →  regression.py  →  persistence.py
   (risk/return)  (factor alpha)    (persistence & robustness)
            │
        export.py  →  CSVs  →  Tableau Public dashboard
```

---

## Data warehouse (star schema)

| Table | Rows | Description |
|---|---|---|
| `dim_fund` | 18 | Fund name, firm, active/passive, category, benchmark, expense ratio |
| `dim_date` | 2,985 | Calendar attributes (year, quarter, month, weekday) |
| `fact_daily_prices` | 53,640 | Adjusted close and daily return. Primary key: (`ticker`, `date`) |
| `fact_factors` | 2,953 | Fama-French 5 factors + momentum + risk-free rate |
| `fact_rates` | 2,964 | FRED 3-month T-bill (DTB3), converted to a daily rate |

The analysis writes three results tables back to the database: `fund_metrics`, `fund_alphas` and `fund_persistence`.

**Snowflake** holds a full mirror of the schema, plus a SQL view (`V_ANNUAL_RETURNS`, built with `MAX_BY` and `LAG`) that computes calendar-year returns. Its output matched the Python results exactly, which gives an independent check on the pipeline. The connection uses RSA key-pair authentication.

---

## Methods

| Step | What it measures | How |
|---|---|---|
| **Risk & return** (`metrics.py`) | CAGR, volatility, max drawdown, Sharpe ratio | Daily returns, annualised with 252 trading days. Sharpe uses excess returns over the T-bill |
| **Relative performance** | Beta, tracking error, information ratio | Each active fund vs its passive benchmark |
| **Factor alpha** (`regression.py`) | Return not explained by market, size, value, profitability, investment or momentum exposure | OLS on the Fama-French 5 factors + momentum, with Newey-West (HAC) standard errors |
| **Uncertainty** | 95% confidence interval for alpha | Bootstrap, 1,000 resamples |
| **Multiple testing** | Controls false discoveries across 12 funds | Benjamini–Hochberg FDR correction |
| **Persistence** (`persistence.py`) | Do the winners stay winners? | Spearman rank correlation of alpha, 2015–2020 vs 2021–2026 |
| **Robustness** | Does the model choice matter? | 3-factor vs 6-factor alpha ranks |

---

## Data quality

`quality.py` runs 17 checks before anything is loaded. They include missing values, duplicate keys, non-positive prices, daily moves above 15%, date gaps, factor value ranges, data staleness, fee ranges, and whether every benchmark is a passive fund in the dataset.

A cross-check against Morningstar's calendar-year returns (e.g. SPY 2022: −18.18%) confirms the price data.

---

## Limitations

- **VWELX is a balanced fund** (about 1/3 bonds), while the Fama-French factors cover equities only, so its alpha is less meaningful.
- **FLPSX's benchmark may be mismatched:** the fund is mid-cap value, while IWR is a mid-cap blend.
- **Small sample:** 12 funds over about 11 years. The test has limited power to detect modest skill.
- **Survivorship bias:** only funds that still exist today were included, so the active fund results are probably flattering.
- **Risk-free rate:** the Fama-French RF (1-month bill) and the FRED DTB3 (3-month bill) differ slightly. FRED is used for Sharpe ratios, Fama-French for the regressions.

---

## How to run

**1. Set up**
```bash
git clone https://github.com/Timer-Senarith/fund-risk-analytics.git
cd fund-risk-analytics
python -m venv .venv
source .venv/bin/activate
pip install yfinance pandas-datareader pandas numpy sqlalchemy "psycopg[binary]" \
            python-dotenv statsmodels "snowflake-connector-python[pandas]"
```

**2. Credentials:** create a `.env` file in the project root. It is git-ignored, so never commit it.
```
NEON_URL=postgresql://<user>:<password>@<host>/<database>
SNOWFLAKE_ACCOUNT=<account-identifier>
SNOWFLAKE_USER=<login-name>
SNOWFLAKE_PRIVATE_KEY_PATH=/path/to/rsa_key.p8
```

**3. Run the pipeline in order**
```bash
python src/extract.py          # download prices, factors and rates to data/raw/
python src/quality.py          # run the 17 data-quality checks
python src/load.py             # build and load the star schema into Neon
python src/load_snowflake.py   # optional: mirror to Snowflake and create the view
python src/metrics.py          # risk/return metrics → fund_metrics
python src/regression.py       # factor regressions → fund_alphas
python src/persistence.py      # persistence and robustness → fund_persistence
python src/export.py           # export CSVs for Tableau to dashboard/data/
```

---

## Project structure

```
fund-risk-analytics/
├── config/
│   └── funds.csv            # fund universe: 18 funds, 12 active, plus benchmarks
├── src/
│   ├── extract.py
│   ├── quality.py
│   ├── load.py
│   ├── load_snowflake.py
│   ├── metrics.py
│   ├── regression.py
│   ├── persistence.py
│   └── export.py
├── dashboard/               # Tableau workbook and exported CSVs
└── README.md
```

---

## Tech stack

Python (pandas, statsmodels, NumPy) · PostgreSQL (Neon) · Snowflake · SQLAlchemy · Tableau Public · Git

*Data sources: Yahoo Finance, the Kenneth R. French Data Library, and FRED (Federal Reserve Bank of St. Louis). This project is for educational purposes only and is not investment advice.*
