# Source 5 — India Gallium & Germanium Imports (HS 8112)

**Role:** Upstream mineral and precursor input proxy for `Gallium_Germanium_Export_Restrictions` (HS 8112: Beryllium, chromium, germanium, vanadium, gallium, hafnium, indium, niobium, rhenium and thallium, and articles thereof, including waste and scrap).  
**Verification date:** 2026-09-05  
**Decision:** **Sourced Baseline from UN Comtrade Annual Trade Statistics** (Reporter: India [699], Partner: World [0], Flow: Imports, CmdCode: 8112).

## Baseline Values (2022 Full Calendar Year)

- **Total Sourced Import Turnover (HS 8112)**: **$66.61M USD**
- **Rupee Conversion @ ₹83.0/USD**: **₹552.84 Crore** (Audited constant: `SOURCED_HS8112_BASELINE_CRORE = 552.86` Cr)
- **Top Origin Concentration**: China Direct = **36.2%** ($24.11M USD / ₹200.1M INR equivalent).
- **Upstream Refining Concentration Penalty**: Disclosed at $C_{\text{upstream}} = 0.900$ reflecting China's ~80–90% global high-purity gallium extraction monopoly.
- **Unhedged Exposure Weight**: $W_{\text{unhedged}} = 0.75$.
- **Resulting Dependency Ratio ($DR$)**: $0.793$ (calculated via `compute_dependency_ratio(0.362, upstream_concentration_penalty=0.900, unhedged_exposure_weight=0.75)`).

## UN Comtrade API Query Shape

- **Endpoint**: `https://comtradeapi.un.org/public/v1/preview/C/A/HS`
- **Parameters**:
  - `reporterCode`: `699` (India)
  - `partnerCode`: `0` (World)
  - `period`: `2022`
  - `cmdCode`: `8112`
  - `flowCode`: `M` (Imports)
- **Primary Data File**: `data/processed/comtrade_india_baseline.json`

## Known Limitations

1. **Tariff Basket Aggregation**: HS 8112 bundles gallium and germanium together with beryllium, chromium, vanadium, hafnium, indium, niobium, rhenium, and thallium. Disaggregated national customs tariff items (e.g. HS 8112.92 for unwrought gallium) require DGCIS TradeStat 8-digit data.
2. **2023–2024 Trade Release Lag**: 2023 records in the UN Comtrade public preview tier remain partial; 2024 full-year data is pending official release. Sourced full-year 2022 baseline is adopted to maintain absolute quantitative integrity rather than falling back to assumed figures.

## How to Regenerate

Run the project Comtrade data sync script:
```bash
python scripts/fetch_comtrade_data.py
```
This updates `data/processed/comtrade_india_baseline.json` and records timestamped trade turnover.
