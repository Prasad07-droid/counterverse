# Source 8 — USD/INR exchange rate (FRED)

**Role:** Confounder + cost-engine input.  
**Verification date:** 2026-09-04  
**Decision:** Keep specified series **DEXINUS** as PRIMARY (daily → monthly mean). Document **EXINUS** as a convenience monthly series with inverted units.

## PRIMARY (as specified)

- Daily: https://fred.stlouisfed.org/series/DEXINUS  
- CSV: https://fred.stlouisfed.org/graph/fredgraph.csv?id=DEXINUS  
- Direct text table also exists on FRED (`/data/SERIESID`).

**Frequency:** Daily. Resample to **monthly mean** in processing.  
**Units (DEXINUS):** US dollars per Indian rupee (confirm on the FRED series page at download time).

This environment: FRED CSV fetch **timed out**. Retry in Phase 2.

## Related series (not a silent substitute)

FRED **EXINUS** is **Indian rupees per US dollar**, **monthly** averages of daily noon buying rates.

Sample from FRED EXINUS table page (https://fred.stlouisfed.org/data/EXINUS), retrieved via public FRED listing 2026-09-04:

| DATE | VALUE |
|------|-------|
| 1973-01-01 | 8.0041 |
| 2026-07-01 | 95.8573 |

Units: **INR per 1 USD**, NSA, monthly. Source: Board of Governors G.5.

If the team uses EXINUS to skip resampling, **say so** — it is not DEXINUS. Do not mix INR/USD and USD/INR without converting.

## Known issues

Missing daily observations around holidays. Preliminary current-month values exist on FRED. Weekend gaps: use business-day mean.
