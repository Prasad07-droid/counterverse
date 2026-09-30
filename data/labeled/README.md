# Human-Labeled Held-Out Evaluation Scaffold

The `dev/` and `test/` files are intentionally empty except for their headers. Do not copy the 15 synthesized benchmark labels into these files; held-out evaluation requires independently collected headlines and human annotation.

## Required process

1. Add a real headline, stable source URL, and source date. Do not add invented headlines or citations.
2. Assign the row to `dev` or `test` before looking at model outputs.
3. Two annotators independently fill their own `is_disruption`, `disruption_type`, and `risk_level` columns.
4. Leave the other annotator's columns hidden during independent labeling.
5. If the two binary labels disagree, a human adjudicator fills `adjudicated_is_disruption` and records a short note. The evaluation script excludes unresolved disagreements.
6. Keep every annotator column empty until a human has made that judgment. Models must never populate these columns.

Accepted binary values are `true`/`false`, `yes`/`no`, or `1`/`0`.

Run after human labeling:

```bash
python scripts/evaluate_heldout.py
python scripts/evaluate_heldout.py --include-qwen  # CUDA GPU only
```

The Qwen arm is marked `not_run` when CUDA is unavailable. CPU-Qwen execution is intentionally out of scope.
