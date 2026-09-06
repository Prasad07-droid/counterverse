# Source 2 — OEM monthly production (Maruti, Tata, M&M)

**Role:** Case-study calibration + precedent library (not the primary Y series).  
**Verification date:** 2026-09-04  
**Decision:** **KEEP PRIMARY** (BSE / company regulatory filings). Fallback aggregators only after one-point BSE cross-check.

## PRIMARY (selected)

- Maruti Suzuki India Ltd. production/sales: BSE filings + https://www.marutisuzuki.com/ (media / investors)
- Tata Motors: BSE + https://www.tatamotors.com/investors/
- Mahindra & Mahindra: BSE + company press notes

**Bulk / CSV:** **No official bulk monthly CSV** for 2019–present across OEMs. Expect a **hand-built panel** from monthly filings (same effort class as SIAM transcription).

**Frequency:** Monthly, target 2019 onwards.  
**Units:** Vehicles (units), sometimes split PV / LCV.

## Sample row (real; secondary news citing a regulatory filing — must re-pull the BSE PDF in Phase 2)

News citing MSI regulatory filing (Times of India, Oct 2021):  
https://timesofindia.indiatimes.com/auto/news/maruti-suzuki-reports-51-drop-in-production-in-september/articleshow/86957478.cms

| oem | month | production_units | note |
|-----|-------|------------------|------|
| Maruti Suzuki India | 2020-09 | 166086 | cited as year-ago in the Sept 2021 filing coverage |
| Maruti Suzuki India | 2021-09 | 81278 | “electronic components shortage”; ~51% YoY drop |

This sample is **news quoting a filing**, not the filing itself. Phase 2 must save the BSE PDF/HTML and replace `source_url` with the exchange document.

## FALLBACK

- moneycontrol.com / screener.in company pages (secondary aggregators)
- **Rule:** cite as secondary; cross-check **one** overlapping month against the original BSE filing before trusting the series.

## Known issues

- Definitions differ (wholesale vs production; include/exclude Gujarat contract manufacture).
- Do not treat OEM units as interchangeable with IIP NIC-29.
