# Source 1 — MoSPI Index of Industrial Production (IIP)

**Role:** Primary outcome proxy for `OEM_Production_Drop` / Production_Drop (Y).  
**Verification date:** 2026-09-04  
**Decision:** **KEEP PRIMARY** (e-Sankhyiki). Fallback data.gov.in catalog is stale / not a usable monthly bulk series.

## PRIMARY (selected)

- Portal: https://esankhyiki.mospi.gov.in/
- IIP product page: https://esankhyiki.mospi.gov.in/macroindicators?product=iip
- Official Python client (optional): `mospi-esankhyiki` — https://pypi.org/project/mospi-esankhyiki/
- MoSPI press releases also publish NIC 2-digit tables and point to the same portal.

**Bulk / CSV:** Custom download and API exist on e-Sankhyiki (not a single static all-years CSV sitting on a public HTTP URL). Programmatic access via portal filters or `esankhyiki.get_data(dataset="IIP", ...)`.

**Filters to apply in Phase 2:**
- Frequency: Monthly
- Series: NIC 2-digit manufacturing
- Codes: NIC **29** (motor vehicles, trailers and semi-trailers) and NIC **26** (computer, electronic and optical products)
- Start: April 2012 if the **2011-12 base** series is used; **do not mix bases without documenting a splice**

**Units:** Index, base year = 100 for the chosen series.

## Sample row (real, from MoSPI press release, NOT invented)

Source PDF: MoSPI “Quick Estimates of IIP” April 2026, Statement II-A, Base **2022-23 = 100**.  
URL pattern: https://www.mospi.gov.in/uploads/latestReleases/ (filename hashed; retrieved 2026-09-04)

| NIC | Description | Weight | Apr'25 | Apr'26* | Cum 2024-25 | Cum 2025-26 | YoY Apr % | Cum % |
|-----|-------------|--------|--------|---------|-------------|-------------|-----------|-------|
| 29 | Manufacture of motor vehicles, trailers and semi-trailers | 6.417 | 116.0 | 130.8 | 112.8 | 124.5 | 12.7 | 10.4 |
| 26 | Manufacture of computer, electronic and optical products | 2.085 | 137.2 | 138.7 | 134.2 | 144.4 | 1.1 | 7.6 |

`*` Quick Estimate. Figures for April 2026 are Quick Estimates per the press note.

## FALLBACK (rejected for bulk history)

- Catalog: https://data.gov.in/catalog/nic-2-digit-level-and-sectoral-monthly-indices-all-india-index-industrial-production
- Observed 2026-09-04: “No Result Found” on zip download UI; published 2013, last updated **2020**. **Schema does not match** a live 2012–present monthly series.
- **Do not silently use this as Y.** Keep as a citation of why PRIMARY was required.

## Known issues

1. **Base-year revision (2026):** MoSPI is moving IIP from base **2011-12** to **2022-23** (TAC-IIP; new series dissemination noted in MoSPI FAQs, May 2026). NIC 2-digit labels in the new series use **NIC 2025**. This is a **series break**. For a 2012–present panel, prefer one consistent base, or document an overlap-window splice. Do not treat 2011-12 and 2022-23 index levels as comparable.
2. Quick Estimates are revised later. Pin the vintage date in the download filename.
3. IIP is an **index of production**, not OEM unit counts. It is a proxy for Y, not Maruti/Tata volumes.

## How to regenerate

Download monthly NIC-2 IIP from e-Sankhyiki for NIC 26 and 29; save under `data/raw/iip_mospi/` (gitignored). Record the exact API/filter JSON in this file when Phase 2 runs.
