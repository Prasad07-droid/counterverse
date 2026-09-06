# Annotation agreement log

## Annotation Provenance & Agreement

### Scenario Authorship
All 15 synthesized scenarios in `data/synthesized_scenarios.json` 
were authored by a single annotator (project author) based on the 
5 disruption category taxonomy defined in AlMahri et al. (2026) 
Appendix A.

### Single-Annotator Limitation
No independent second reviewer validated the ground-truth labels 
for these 15 scenarios. This is a known limitation: inter-annotator 
agreement (Cohen's Kappa) could not be computed.

**Implication:** The precision/recall/F1 metrics in Table 5 are 
computed against single-author ground truth. Systematic labeling 
bias from the author cannot be ruled out.

**Mitigation:** The scenario set includes 4 explicitly benign 
control cases (False Positive controls) designed to test 
over-triggering. The SLM flagged all 4 as disruptions, confirming 
the known precautionary bias — this result is consistent with 
expectations and not attributable to label manipulation.

**Future Work:** A second independent annotator reviewing the 15 
scenarios would enable Cohen's Kappa computation and strengthen 
the evaluation's credibility.
