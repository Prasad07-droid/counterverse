# Source 5 — WSTS Historical Billings (global semiconductor)

**Role:** Global chip supply **proxy** (not Y).  
**Verification date:** 2026-09-04  
**Decision:** **KEEP PRIMARY.** Full historical billings Excel is **free, no login** (as of this date). Fallback PDFs not required unless the XLSX later becomes members-only.

## PRIMARY (selected)

- Page: https://www.wsts.org/67/Historical-Billings-Report
- Stated 2026-09-04: “Four decades of WSTS statistics … free download … latest data from **June 2026**. No login is required.”
- Files: Historical Billings Report **XLSX**; Monthly data 3MMA **PDF**
- Content described by WSTS: monthly data and 3-month moving averages of total semiconductor **revenues** by region (Americas, Europe, Japan, Asia Pacific)

**Units:** typically USD millions (confirm from the XLSX header in Phase 2).

## Sample row

XLSX was not downloaded in Phase -1 (large binary; gitignored anyway). **Schema from the publisher page:**

| period | region | billings_or_3mma |
|--------|--------|------------------|
| YYYY-MM | Americas / Europe / Japan / Asia Pacific | numeric revenue |

Paste a real first data row from the June 2026 XLSX here after Phase 2 download.

## FALLBACK (not activated)

Free monthly press-release PDFs only if the XLSX becomes paywalled. Partial series is acceptable for this proxy.

## Known issues

WSTS copyright restricts republication. Store locally, cite, do not scrape into a public app as a redistributed dataset. Asia Pacific billings ≠ India auto MCU supply.
