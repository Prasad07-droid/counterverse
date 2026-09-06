# Source 6 — NY Fed Global Supply Chain Pressure Index (GSCPI)

**Role:** Treatment-variable **proxy** for the causal model (not a company shock series).  
**Verification date:** 2026-09-04  
**Decision:** PRIMARY confirmed. No fallback required.

## PRIMARY

- Product page: https://www.newyorkfed.org/research/policy/gscpi/
- Documented interactive CSV (used by third-party clients):  
  https://www.newyorkfed.org/medialibrary/research/interactives/data/gscpi/gscpi_interactive_data.csv
- Methodology: Benigno, di Giovanni, Groen, Noble, NY Fed Staff Report 1017 (May 2022)

**Frequency:** Monthly, from 1997.  
**Units:** Index in **standard deviations** from historical average (not percent, not rupees).

**Bulk / CSV:** Yes. This environment received **HTTP 500** fetching the CSV on 2026-09-04; the URL is still the documented public file. Retry in Phase 2 from the laptop browser.

## Sample row (schema from documented wide-format CSV)

Third-party parsers describe: **wide format**, each column a revision vintage, **last column = latest estimate**; rows are dates.

Example **interpretation** (not a fabricated latest vintage): values `> 0` = above-average pressure. Peak-stress months in 2021 are the High-severity calibration analogue (GSCPI ≈ 3 SD class in the project brief). **Paste the actual CSV cells after a successful download.**

## Known issues

GSCPI is global, not India-auto-specific. Using it as treatment proxy is an **assumption** (document in `docs/assumptions_and_dag.md`). Revisions change history when the Fed updates the interactive file — pin download date.
