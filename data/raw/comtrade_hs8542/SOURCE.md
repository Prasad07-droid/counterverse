# Source 4 — India semiconductor-related imports (HS 8542 + HS 8541)

**Role:** Input proxy for `Semiconductor_Shortage`.  
**Verification date:** 2026-09-04  
**Decision:** **SWITCH DEFAULT TO FALLBACK (UN Comtrade Plus)** for bulk monthly history. TradeStat is a **web form**, not a bulk CSV.

## PRIMARY (verified, not used as bulk default)

- TradeStat commodity-wise import: https://tradestat.commerce.gov.in/meidb/commoditywise_import
- Observed 2026-09-04: monthly UI, data advertised **Jan 2018 – Jun 2026**, HS 2/4/6/8 digit, USD million / Rs crore / quantity, FY or CY.
- **No monthly bulk file download** of a full HS 8541/8542 panel. Interactive submit-and-view only.
- Per project rule: if tradestat has no monthly bulk view, **do not hunt**; use Comtrade as default.

**Logged switch:** PRIMARY remains useful for **one-month cross-check**. Bulk series = FALLBACK.

## FALLBACK (selected for bulk)

- https://comtradeplus.un.org/TradeFlow
- Free registration for API key: https://uncomtrade.org/docs/how-to-create-an-account/
- API docs: https://uncomtrade.org/docs/un-comtrade-api/
- Example (preview-style) query shape: frequency **M**, classification **HS**, reporter **India (M49 699)**, partner **World (0)**, flow **M** (imports), `cmdCode` **8542** and **8541**, `period` YYYYMM.

**Units:** typically USD trade value; quantity if reported. Convert/document units in the processed file.

## Sample row (schema, not a live pull — Comtrade fetch timed out from this environment)

Until Phase 2 registration + API pull, the **TradeStat UI schema** (observed) is:

| field | example meaning |
|-------|-----------------|
| HSCode | 8542 |
| Commodity | Electronic integrated circuits |
| month/year | e.g. Mar 2021 |
| value | USD million or Rs crore (user-selected) |
| %Growth | vs year-ago month |

**Do not invent a 2021 dip number here.** Pull HS 8542 India imports for 2021-03 vs 2019-03 in Phase 2 and paste a real API/UI row.

## Known issues

- India monthly availability on Comtrade can lag and is not guaranteed for every YYYYMM.
- HS 8542 is broader than automotive MCUs.
- Free Comtrade API has rate limits; needs a **free** subscription key (not a paid runtime API for the dashboard). ✅ **Confirmed acceptable 2026-09-04** — key used in data download scripts only.

## How to regenerate

1. Register on Comtrade Plus (free).
2. Pull monthly India imports HS 8541 + 8542, partner World.
3. Cross-check one overlapping month on TradeStat UI; record both values in this file.
