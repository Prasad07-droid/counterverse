# Source 3 — SIAM monthly segment production / sales

**Role:** Secondary outcome cross-check.  
**Verification date:** 2026-09-04  
**Decision:** **PRIMARY page exists; FALLBACK (manual transcription) is the operational method.** No bulk CSV found.

## PRIMARY

- Press list: https://www.siam.in/press-release.aspx?mpgid=48&pgidtrail=50
- Example (December 2024 performance): https://www.siam.in/pressrelease-details.aspx?mpgid=48&pgidtrail=50&pid=576

**Bulk / CSV:** **Not found.** Monthly HTML/PDF press notes only. Budget 2–3 hours of manual entry as specified.

## Sample row (real, from SIAM December 2024 press page)

| month | metric | value | unit |
|-------|--------|-------|------|
| 2024-12 | Production (PV + 3W + 2W + quadricycle, as defined in that note) | 1921268 | vehicles |
| 2024-12 | Domestic sales, Passenger Vehicles | 314934 | vehicles |
| 2024-12 | Domestic sales, Three-wheelers | 52733 | vehicles |
| 2024-12 | Domestic sales, Two-wheelers | 1105565 | vehicles |

Footnotes on SIAM pages exclude some luxury OEM data in some months — copy footnotes into the CSV.

## FALLBACK (selected as how we will actually build the series)

Manually transcribe monthly press figures into `data/raw/siam/siam_monthly.csv` (gitignored). This is expected, not a last resort.

## Known issues

Segment definitions and footnotes change. Keep a `notes` column. This is **not** a company procurement series.
