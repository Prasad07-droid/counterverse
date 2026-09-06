# Source 9 — ACMA industry performance (calibration constants only)

**Role:** Annual calibration constants (electronics import share, China dependency %, industry turnover). **Not a monthly time series.**  
**Verification date:** 2026-09-04  
**Decision:** **KEEP PRIMARY** (ACMA press + annual reports). Do not average with SIAM.

## PRIMARY (selected)

- Statistics page: https://www.acma.in/auto-component.php  
- Annual reports: https://acma.in/annual-report.php  
- FY 2024-25 performance press PDF: https://www.acma.in/uploads/press-release/Press%20Release%20FY25.pdf  
- H1 FY26 press PDF: https://www.acma.in/uploads/press-release/FINAL%20-%20Press%20Release%20-%20ACMA_H1_FY26.pdf  

`acma.in/publications` redirects/overlaps with these publication URLs.

## Sample row (real, FY2024-25 press, 8 Jul 2025)

| constant | value | unit | source |
|----------|-------|------|--------|
| Auto component industry turnover FY2024-25 | 6.73 | lakh crore INR | ACMA Industry Performance Review FY25 press |
| Same, USD | 80.2 | billion USD | same |
| YoY growth | 9.6 | percent | same |
| Sales to OEMs | 5.70 | lakh crore INR | same |
| Imports | 22.4 | billion USD | same |
| Trade surplus | 453 | million USD | same |

These are **annual**. Do not interpolate into monthly Y.

## FALLBACK (not activated)

SIAM annual report for the **same named constants** only if the ACMA PDF cannot be retrieved. Cite one source, do not blend.

## Known issues

Electronics-import-share / China-dependency % may sit in slide decks not the short press note. If a constant is missing, log **ASSUMPTION** in `docs/assumptions_and_dag.md` rather than scraping a blog.
