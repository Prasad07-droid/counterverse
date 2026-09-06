# Source 10 — Supplier concentration / HHI (UDYAM + ACMA directory)

**Role:** `Supplier_HHI` confounder (static or slowly updated).  
**Verification date:** 2026-09-04  
**Decision:** **FALLBACK likely operational** — ACMA member directory access not verified as a bulk public file. Plan HHI from UDYAM Pune + Thane as a **lower-bound proxy**.

## PRIMARY (partial)

- UDYAM / MSME catalog: https://www.data.gov.in/catalog/udyam-registration-msme-registration  
- Observed: catalog exists; zip UI showed “No Result Found” in this verification pass; practitioners report **login + district API/spreadsheet**, not a single national CSV.
- Independent write-up of Pune district pull (secondary): https://blog.deasra.in/what-does-udyam-registration-data-reveal-about-pune-district/  
  Reported fields: state, district, registration date, pincode, address, **NIC-5 activity codes**. **No turnover / employment / investment.** ~9.1 lakh Pune rows cited as of 20 Mar 2026 (that blog’s vintage).
- MSME district dashboard: https://dashboard.msme.gov.in/udyam_dist_wise.aspx (aggregates, not unit-level HHI)

**ACMA member directory:** not confirmed as a downloadable public roster in this pass. Treat as **blocked until a teammate with access logs a yes**.

## Sample row (schema from UDYAM unit-level descriptions — not a live API dump)

| state | district | registration_date | pincode | nic5_codes |
|-------|----------|-------------------|---------|------------|
| Maharashtra | Pune | (ISO date) | (6-digit) | (list) |

Filter NIC codes related to auto components / electronics (document the code list in Phase 2). HHI = sum of squared shares. Without turnover, **share must be unit-count share**, which is a weak concentration proxy.

## FALLBACK (selected until ACMA roster is in hand)

Compute HHI from UDYAM Pune + Thane **only**. State in processed metadata: **lower-bound / incomplete census, not exhaustive of ACMA organised-sector members.**

## Known issues

data.gov.in APIs often need an **API key** (free registration). That is not a paid dashboard runtime. Unit-count HHI ≠ revenue HHI. UDYAM is not limited to auto-component firms — NIC filter is mandatory.
