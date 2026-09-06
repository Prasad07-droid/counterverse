# Source 12 — Policy texts (SLM test corpus)

**Role:** Policy-type headlines/documents for SLM **testing** (not training labels unless separately annotated).  
**Verification date:** 2026-09-04  
**Decision:** PRIMARY portals exist as **PDF lists**, not a bulk API. Manual download of a small corpus is expected.

## PRIMARY

- DGFT notifications: https://www.dgft.gov.in/CP/?opt=notification  
- DGFT public notices: https://www.dgft.gov.in/CP/?opt=public-notice  
- DGFT circulars / trade notices: same site (`opt=circular`, `opt=trade-notice`)
- CBIC customs circulars: https://www.cbic.gov.in/ (circulars / instructions section — confirm exact landing page when downloading)
- OEM annual reports / concall transcripts: company IR sites (same as Source 2); excerpts only, fair-use for academic annotation

**Bulk / CSV:** No. Each document is a PDF “Download” attachment.

## Sample row (real DGFT listing, 2026-09-04 scrape of notifications table)

| number | date | description |
|--------|------|-------------|
| 27/2026-27 | 05/08/2026 | Introduction of Inventory-based Cross-border E-Commerce Export Framework under FTP |

Store: `data/raw/policy_texts/<id>.pdf` (gitignored) + a manifest CSV with `title, date, url, doc_type`.

## Known issues

Most DGFT items are **not** semiconductor-export controls. Filter by HS / electronics / SCOMET / China / rare earth / magnet keywords. Concall transcripts may be on paid platforms — **do not use paid APIs at runtime**; skip if not free HTML/PDF.
