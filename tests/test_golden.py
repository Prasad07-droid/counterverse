"""Golden regression tests for behavior protected before hardening."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GOLDEN_DIR = PROJECT_ROOT / "tests" / "golden"
CAPTURE_SCRIPT = GOLDEN_DIR / "capture_golden.py"
PIPELINE_GOLDEN = GOLDEN_DIR / "pipeline_outputs.json"
EVALUATION_GOLDEN = GOLDEN_DIR / "evaluation_results.json"
CURRENT_EVALUATION = PROJECT_ROOT / "data" / "evaluation_results.json"
APPROVED_TIER_C_CHANGES = PROJECT_ROOT / "tests" / "approved_tier_c_changes.json"


def _apply_approved_tier_c_changes(expected: dict) -> dict:
    """Apply only explicitly approved deviations to the immutable baseline."""
    approval = json.loads(APPROVED_TIER_C_CHANGES.read_text(encoding="utf-8"))
    changes = approval["changes"]
    scenarios = {row["id"]: row for row in expected["scenarios"]}
    assert set(changes) == set(scenarios)
    for scenario_id, fields in changes.items():
        scenarios[scenario_id]["signal"]["severity_pct"] = fields["severity_pct"]
        scenarios[scenario_id]["signal"]["duration_days"] = fields["duration_days"]
    return expected


def _capture_current_outputs() -> dict:
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = "0"
    completed = subprocess.run(
        [sys.executable, str(CAPTURE_SCRIPT)],
        cwd=PROJECT_ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def test_pipeline_outputs_match_pre_hardening_golden() -> None:
    expected = json.loads(PIPELINE_GOLDEN.read_text(encoding="utf-8"))
    expected = _apply_approved_tier_c_changes(expected)
    actual = _capture_current_outputs()
    assert actual == expected


def test_evaluation_results_match_pre_hardening_golden() -> None:
    expected = json.loads(EVALUATION_GOLDEN.read_text(encoding="utf-8"))
    actual = json.loads(CURRENT_EVALUATION.read_text(encoding="utf-8"))
    assert actual == expected
