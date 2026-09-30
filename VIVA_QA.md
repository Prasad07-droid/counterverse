# CounterVerse Viva / Reviewer Q&A

These answers describe the current repository, not an aspirational production system.

## 1. Is CounterVerse a forecast of future supply-chain losses?

No. It is a scenario simulator. `src/module_d_mc.py` samples calibrated stress distributions conditional on a supplied scenario; it does not fit or extrapolate a time-series forecasting model. The dashboard labels this explicitly as “Scenario simulator — not a forecast.”

## 2. Does the project discover causal relationships from data?

No. `src/module_c_causal.py` applies a domain-informed weighted index and maps it to outcome-state probabilities. The graph and formula encode assumptions; they do not identify causality through interventions, confounder adjustment, or do-calculus.

## 3. Is the grounding layer a full GraphRAG system?

No. `src/grounding_graph.py` performs deterministic alias resolution and lookup against a static NetworkX graph. There is no embedding index, community summarization, vector retrieval, or retrieved context generation. The precise term used in project-facing text is “graph-grounded entity verification.”

## 4. What is actually in the verification graph?

The code builds 30 nodes and 69 directed edges. `get_graph_summary()` reports 14 `operates_in`, 8 `depends_on`, 14 `supplies`, 8 `requires`, 12 `belongs_to`, 9 `exports`, and 4 `imports_from` edges. The locked integrity hash is `31f67108669b9208`.

## 5. Is the Dependency Ratio wholly empirical?

No. Direct and transit shares are data-informed by the repository’s UN Comtrade baseline, but upstream concentration (`C_upstream`) and the unhedged-exposure weight (`W_unhedged = 0.75`) are assumptions. The score is therefore only partially data-informed.

## 6. What DR outputs are protected by tests?

The current formula produces 0.560 for China IC exposure, 0.793 for gallium/germanium, 0.555 for Taiwan IC exposure, and 0.430 for South Korea IC exposure. Tests lock those values; hardening does not change them.

## 7. Is Exposure Depth calculated as tier divided by four?

No. The code uses a discrete lookup: raw material 1.00; IC/wafer/microcontroller/ECU 0.75; automotive sensor 0.25; and unverified fallback 0.50. Documentation was corrected to match the code.

## 8. Does HS 8112 measure only gallium and germanium?

No. HS 8112 is a broad tariff basket that includes several other metals and related articles, waste, and scrap. CounterVerse uses its aggregate value only as an upstream stress proxy, not as a measured gallium/germanium procurement total.

## 9. Are automotive microcontrollers made from gallium or germanium?

Mainstream automotive MCUs are silicon-based. The model treats Ga/Ge relevance as a stress-test pathway through compound-semiconductor applications such as GaN, GaAs, and SiGe. It must not be read as a claim that conventional silicon MCUs use Ga/Ge feedstock.

## 10. Are the Monte Carlo distributions fitted to historical losses?

No. `src/module_d_mc.py` labels them `calibrated_estimate`. State-specific normal distributions and the procurement premium range are modeling assumptions, not econometric fits.

## 11. Why use 10,000 Monte Carlo draws?

It provides stable numerical summaries for the chosen assumed distributions at low computational cost. More draws reduce sampling noise but cannot repair misspecified assumptions; 10,000 is not evidence of empirical certainty.

## 12. Is Monte Carlo output reproducible?

Yes for a given explicit seed and environment. `run_monte_carlo()` uses a seeded NumPy random state, and tests compare complete sample arrays across repeated runs.

## 13. Is headline-derived severity reproducible across separate Python processes?

Yes after the explicitly approved Tier C hardening change. `_map_fast_params()` derives a stable integer seed from the first eight bytes of `SHA-256(headline)` and passes it to a local `random.Random` instance. Tests execute extraction under different `PYTHONHASHSEED` values and require identical severity and duration.

## 14. Why are there two SIAM numbers in the repository?

The data-layer test case uses a 37.46% target from `SIAM_2021_GROUND_TRUTH`, while the dashboard separately displays a 41.2% target. Both pre-existing paths are captured by golden tests. Consolidating them into one canonical JSON is a Tier C change and has not been performed.

## 15. Does the SIAM comparison prove predictive accuracy?

No. Severity, duration, and node selection were configured with knowledge of the event. It is a calibration plausibility check, not held-out validation.

## 16. How strong is the 0.933 macro F1 claim?

It is the stored result of an adapted evaluation protocol over 15 synthesized scenarios: 11 disruptions and 4 benign controls. The sample is small, authored by one annotator, and sensitive to individual label changes. It is not a population-level performance estimate.

## 17. Has an independent held-out evaluation been completed?

No. `data/labeled/dev` and `data/labeled/test` are intentionally empty scaffolds. `scripts/evaluate_heldout.py` requires two-annotator agreement or adjudication and can report bootstrap intervals once humans provide sourced labels.

## 18. Does the current stored evaluation prove Qwen performance on any machine?

No. `data/evaluation_results.json` records a particular local GPU run. Runtime availability depends on PyTorch, CUDA, model weights, and hardware. Cloud mode falls back to the deterministic fast extractor.

## 19. What does the original PCaR value represent?

The protected existing metric is simulated production-drop percentage multiplied by an allocated procurement baseline and a premium multiplier. It is a stressed procurement-exposure metric, not an audited accounting loss or vehicle-output valuation.

## 20. How are extra procurement cost and lost output now distinguished?

The additive extra-procurement metric uses only the premium above baseline: disrupted procurement spend multiplied by `(premium - 1)`. Lost output is calculated only if a caller supplies a separate output-value baseline; otherwise those keys are `null`. Procurement spend is never silently relabeled as output value.

## 21. Are OEM dependency ratios audited BOM facts?

No. The 0.38–0.45 ratios are heuristic proxies. Market-share scaling and arithmetic boundedness do not validate those inputs. Real enterprise use requires confidential BOM/procurement data or expert validation.

## 22. Why does the project still use 2022 UN Comtrade data?

Because 2022 is the latest complete full-year HS 8542/8112 extraction fetched, checked, and stored in this repository. This is not a claim that later UN Comtrade data is unreleased. The baseline predates China’s August 2023 gallium/germanium export controls.

## 23. How resilient is news ingestion?

`src/data_sources.py` uses a four-tier path: GDELT, Google News RSS, SQLite cache, then a static fallback. Static illustrative entries are explicitly marked as samples and have no fabricated external URLs. Public feeds still have no availability or provenance guarantee.

## 24. Is the application production-secure?

No. It sanitizes a set of prompt-injection patterns and avoids requiring credentials for basic operation, but it has no authentication, authorization, application-level rate limiting, or CI security pipeline in this checkout. It is an academic demonstrator.

## 25. What would be required before enterprise deployment?

At minimum: independently labeled held-out data, domain-expert review, primary-source verification, refreshed trade data, empirical distribution fitting, real BOM/output baselines, authentication and authorization, operational telemetry, monitoring, model-risk controls, and a prescriptive workflow validated by procurement teams.
