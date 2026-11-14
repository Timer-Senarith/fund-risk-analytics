# Investment Memo: Do Active Fund Managers Earn Their Fees?

**From:** Timer Senarith · **Date:** November 2026 · **Period studied:** Jan 2015 – Sep 2026
**Dashboard:** [Tableau Public](https://public.tableau.com/views/Book1_17945886122090/Doactivefundmanagersearntheirfees20152026) · **Code:** [GitHub](https://github.com/Timer-Senarith/fund-risk-analytics)

---

## Recommendation

**Default to low-cost index funds.** Over 2015–2026, none of the 12 well-known active US equity funds tested delivered outperformance that can be distinguished from luck after fees. A strong track record on its own is not enough evidence of skill to justify paying active fees.

## The question

Do active managers add value once we account for (1) fees, (2) the risk factors that explain most of their returns, and (3) the chance that some funds look good by luck?

## Approach

- **Data:** daily total-return prices for 18 funds (12 active, 6 passive benchmarks), Fama-French 5 factors + momentum, and FRED T-bill rates. All of it passes 17 automated quality checks, is stored in a PostgreSQL star schema, and was cross-checked against Morningstar and a Snowflake SQL view.
- **Alpha:** the return left over after regressing each fund's excess return on six risk factors (market, size, value, profitability, investment, momentum), with Newey-West standard errors. Returns are net of fees.
- **Luck vs skill:** bootstrap 95% confidence intervals, plus a Benjamini–Hochberg correction for testing 12 funds at once.
- **Persistence:** do 2015–2020 winners keep winning in 2021–2026?

## Key findings

1. **Most active funds lost to the factors after fees.** 9 of 12 have negative annual alpha, ranging from −0.5% (TRBCX) to −2.0% (FMAGX, Magellan).
2. **No fund's alpha survives the multiple-testing correction.** FBGRX looks impressive on its own: +3.4% a year, p = 0.03, with a 95% range of +0.2% to +6.4%. But with 12 funds tested, one result like this is expected by chance, and its adjusted p-value is 0.33. FCNTX (Contrafund), the best on Sharpe ratio (0.73), has +1.3% alpha, which is not significant (p = 0.26).
3. **Past performance is a weak guide.** The rank correlation of alpha between the two halves is only 0.40, and 10 of 12 funds had negative alpha in 2021–2026. FBGRX was the only fund positive in both halves.
4. **The result is robust.** A simpler 3-factor model ranks the funds almost identically (correlation 0.96). The factors explain 87–97% of daily fund moves, so most "active" return is factor exposure an investor could buy cheaply.

## Implications

- For most allocations, passive exposure (or cheap factor tilts) captures what these funds deliver, at a fraction of the cost.
- Active managers should be judged on factor-adjusted, multiple-testing-aware alpha over long windows, not on raw returns or a single strong period.
- FBGRX is the one fund worth watching: positive in both halves, though not yet statistically proven.

## Limitations

- **Small sample:** 12 funds over about 11 years, so there's low power to detect modest skill.
- **Survivorship bias:** only funds that still exist were tested, which likely flatters the active funds.
- **Model fit:** VWELX holds about 1/3 bonds, but the factors cover equities only. FLPSX (mid-cap value) is benchmarked against a mid-cap blend index.
- **Backward-looking:** these are historical results and not investment advice.
