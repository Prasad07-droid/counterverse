# Source 13 — Disruption event calendar (hand-built)

**Role:** Treatment indicator + precedent-library backbone.  
**File:** `data/processed/events.csv`  
**Verification date:** 2026-09-04  
**Decision:** Hand-built from **public** timelines. Dates are literature/news consensus windows, not company-internal. Severity is an **ASSUMPTION** pending team freeze.

## Columns

`event_name,start_date,end_date,affected_component,severity,source_url`

## Sample row (real dated public source)

COVID India manufacturing shutdown window used in the project brief: Mar–Jun 2020.

| event_name | start_date | end_date | affected_component | severity | source_url |
|------------|------------|----------|--------------------|----------|------------|
| COVID-19 manufacturing shutdown | 2020-03-24 | 2020-06-30 | broad manufacturing / auto | 3 | https://www.mha.gov.in/ (national lockdown orders; pin exact PDF in Phase 2) |

Remaining events are listed in `.cursorrules`. Phase 2 fills `events.csv` with one `source_url` **per row** (WHO/MHA, WSTS/OEM filings, Shanghai municipal notices, MOFCOM Ga/Ge, shipping-insurance Red Sea notes, China rare-earth 2025 measures, Russia-Ukraine industrial-gas reporting). **Do not invent severity as ground truth.**

## Known issues

Windows are inclusive and politically contested (especially Red Sea end date and 2025 magnet measures). Record disagreements in this file rather than averaging silently.
