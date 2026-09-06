# Source 7 — World Bank Pink Sheet (commodity prices)

**Role:** Confounder — copper, aluminium, rubber.  
**Verification date:** 2026-09-04  
**Decision:** PRIMARY confirmed. No fallback required.

## PRIMARY

- Page: https://www.worldbank.org/en/research/commodity-markets
- Observed on that page (search index, 2026-09-04): monthly **XLS** “Monthly prices” (e.g. September 2026 XLS listed alongside Pink Sheet PDF).
- URLs for the XLS include a **hash that changes every month**. Do not hardcode a dead link. Either download from the page or use a wrapper that rediscovers the current URL (e.g. `worldbank-commodities` — optional; pin if used).

**Frequency:** Monthly.  
**Units:** commodity-specific (e.g. copper typically USD / metric ton). Confirm from the “Description” sheet in the workbook.

## Sample row

Full XLS was not stored in Phase -1. From World Bank Pink Sheet PDF editions (CMO related files on thedocs.worldbank.org), the table is a **commodity × period** matrix with Unit in the first columns and monthly averages in later columns (Energy, metals, agriculture blocks).

**Paste one copper / aluminium / rubber line from the downloaded XLS in Phase 2.** Do not invent price levels here.

## Known issues

Some recent months are World Bank estimates and later revised. Rubber vs tyre-grade vs natural rubber series names must be matched explicitly. This is a global price, not an Indian auto-component invoice price.
