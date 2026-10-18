# CounterVerse — Repository Truth & Baseline Audit (Phase 0)

**Date:** 2026-10-18  
**Branch:** `feature/report-v2`  
**Test Suite Status:** 94 passed, 2 skipped, 1 warning (pytest 9.1.1 on Python 3.14.8)  
**Total Test Coverage:** 65% (2513 statements, 871 missed)

---

## 1. Test Suite & Coverage Baseline

### Exact Test Command & Result
```powershell
.\.venv\Scripts\python.exe -m pytest tests/ -v --tb=short
# Result: 94 passed, 2 skipped, 1 warning in 9.00s
```

### Coverage Execution & Result
```powershell
.\.venv\Scripts\python.exe -m pytest tests/ --cov=src --cov=api --cov-report=term --tb=short
# Result: TOTAL Coverage: 65% (2513 statements, 871 missed)
```

#### Per-Module Breakdown
| Module | Stmts | Miss | Cover |
|---|---|---|---|
| `api/__init__.py` | 0 | 0 | 100% |
| `api/main.py` | 338 | 102 | 70% |
| `src/__init__.py` | 0 | 0 | 100% |
| `src/auth.py` | 54 | 32 | 41% |
| `src/config.py` | 90 | 42 | 53% |
| `src/data_sources.py` | 239 | 54 | 77% |
| `src/extra_config.py` | 8 | 0 | 100% |
| `src/grounding_graph.py` | 305 | 89 | 71% |
| `src/metrics.py` | 55 | 33 | 40% |
| `src/module_a_ingest.py` | 86 | 60 | 30% |
| `src/module_b_slm.py` | 316 | 186 | 41% |
| `src/module_c_causal.py` | 163 | 23 | 86% |
| `src/module_d_mc.py` | 75 | 16 | 79% |
| `src/module_e_pcar.py` | 161 | 38 | 76% |
| `src/module_i_report.py` | 450 | 23 | 95% |
| `src/news_scraper.py` | 173 | 173 | 0% |
| **TOTAL** | **2513** | **871** | **65%** |

*(Note: Documentation quoting ~92% coverage was an assertion; actual measured coverage is 65%).*

---

## 2. Phase 1 Claim-by-Claim Audit

| # | Item Description | Status | Source File & Lines | Audit Findings & Evidence |
|---|---|---|---|---|
| **1** | `api/main.py` `get_siam_backtest()` calls `json.load` without `json` import | **VERIFIED** | [api/main.py](file:///c:/Users/Dattaprasad/Videos/sem%207/api/main.py#L856-L875) | Line 865 calls `json.load(f)`, but `json` is not imported at module top or locally in `get_siam_backtest()`. The `NameError` is swallowed by line 866 `except Exception as e:`, causing silent fallback to recomputing on every call. |
| **2** | `src/grounding_graph.py`: `load_graph_overlay()` is never called in `get_grounding_graph()`; custom nodes lost on restart | **VERIFIED** | [src/grounding_graph.py](file:///c:/Users/Dattaprasad/Videos/sem%207/src/grounding_graph.py#L309-L314), [L740](file:///c:/Users/Dattaprasad/Videos/sem%207/src/grounding_graph.py#L740) | `load_graph_overlay()` is defined at line 740, but `get_grounding_graph()` at line 309 only calls `build_grounding_graph()` and does not merge the overlay. Custom nodes persisted via `save_graph_overlay()` are not restored on restart. Base graph hash `31f67108669b9208` passes in `tests/test_golden.py`. |
| **3** | Seed isolation: `calculate_pcar` and `calculate_pcar_custom_bom` use global `np.random.uniform`; leftover `time.sleep(0.1)` | **VERIFIED** | [src/module_e_pcar.py](file:///c:/Users/Dattaprasad/Videos/sem%207/src/module_e_pcar.py#L89), [L107](file:///c:/Users/Dattaprasad/Videos/sem%207/src/module_e_pcar.py#L107), [L489](file:///c:/Users/Dattaprasad/Videos/sem%207/src/module_e_pcar.py#L489) | Line 89 contains `time.sleep(0.1)` artificial latency. Line 107 in `calculate_pcar()` and line 489 in `calculate_pcar_custom_bom()` both draw from global `np.random.uniform` without accepting a `random_seed` or using a local `np.random.default_rng()`. |
| **4** | Broken grounding mapping in `build_report_data()`: reads summary keys at top level and incorrect entity dict keys | **VERIFIED** | [src/module_i_report.py](file:///c:/Users/Dattaprasad/Videos/sem%207/src/module_i_report.py#L268-L284) vs [src/grounding_graph.py](file:///c:/Users/Dattaprasad/Videos/sem%207/src/grounding_graph.py#L621-L639) | `build_report_data()` accesses `grounding.get("verified_count")`, `total_entities`, `verification_rate`, `graph_hash`, `total_nodes`, `total_edges`, but `ground_entities()` nests them inside `grounding["summary"]` and `grounding["summary"]["graph_stats"]`. Furthermore, lines 280-282 check `ent.get("entity")` and `ent.get("in_graph")`, whereas `ground_entities()` outputs `entity_text`, `canonical_name`, and `status == "Graph-Verified"`. This causes entities to always show as "Entity" with "Unverified, needs human review". |
| **5** | `generate_report()` leaks full 10,000 raw samples in `mc_stats` and `data`; `ReportResponse.pcar` carries directive instead of PCaR | **VERIFIED** | [src/module_i_report.py](file:///c:/Users/Dattaprasad/Videos/sem%207/src/module_i_report.py#L969-L972), [api/main.py](file:///c:/Users/Dattaprasad/Videos/sem%207/api/main.py#L731-L741) | `report_data["mc_stats"]` holds the full `mc_result` dictionary which includes the 10,000-element `samples` array. `generate_report()` returns this array in `mc_stats` and `data`. Line 970 maps `"pcar": _sanitize_for_json(report_data["pcar_rec"])`, assigning the cost-adjusted recommendation instead of the financial metrics in `report_data["pcar"]`. |
| **6** | Docs/code drift: Sensitivity baseline score, SIAM targets, and README dashboard/endpoint counts | **VERIFIED** | [data/sensitivity_results.json](file:///c:/Users/Dattaprasad/Videos/sem%207/data/sensitivity_results.json#L5), [src/data_sources.py](file:///c:/Users/Dattaprasad/Videos/sem%207/src/data_sources.py#L467), [tests/golden/capture_golden.py](file:///c:/Users/Dattaprasad/Videos/sem%207/tests/golden/capture_golden.py#L162), [README.md](file:///c:/Users/Dattaprasad/Videos/sem%207/README.md#L144-L165) | 1. Baseline sensitivity score is `0.7825` in `data/sensitivity_results.json`, while documentation asserted `0.752`.<br>2. SIAM 2021 PV production drop is `37.46` in `src/data_sources.py` (actual YoY PV drop), whereas golden test and dashboard code benchmark against `41.2` (modeled P95 tail drop).<br>3. `README.md` lists 4 REST endpoints and 6 Streamlit views, whereas the codebase exposes 11+ REST endpoints and a 3-view React dashboard. |
| **7** | `src/utils/generatePdfReport.ts` usage and real PDF generation architecture | **CONTRADICTED (Import) / VERIFIED (Architecture)** | [src/components/war-room/ExecutiveWarRoom.tsx](file:///c:/Users/Dattaprasad/Videos/sem%207/src/components/war-room/ExecutiveWarRoom.tsx#L29), [L545](file:///c:/Users/Dattaprasad/Videos/sem%207/src/components/war-room/ExecutiveWarRoom.tsx#L545), [src/module_i_report.py](file:///c:/Users/Dattaprasad/Videos/sem%207/src/module_i_report.py#L941) | **Contradiction:** The claim that `src/utils/generatePdfReport.ts` is not imported anywhere is incorrect: line 29 of `ExecutiveWarRoom.tsx` imports `createClientPdfBlob`, and line 545 invokes it as a fallback when the server API is unavailable.<br>**Verification:** The primary server-side pipeline path is indeed `POST /api/v1/generate-report` in `api/main.py` -> `src/module_i_report.py` (`render_pdf_bytes`), generating raw PDF 1.4 without ReportLab and serving via `/static/reports/*.pdf`. `generatePdfReport.ts` should be clearly annotated as an offline client-side fallback. |
