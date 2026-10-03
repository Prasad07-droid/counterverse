import pytest
from src.module_b_slm import _map_fast_params, SEVERITY_RUBRIC

@pytest.mark.parametrize(
    "headline, severity_input, is_disruption, expected_key",
    [
        ("Major earthquake in Japan disrupts supply chain", "CRITICAL", True, "CRITICAL"),
        ("Minor delay at port", "LOW", True, "LOW"),
        ("Routine quarterly earnings reported", "LOW", False, "NON_DISRUPTION"),
    ],
)
def test_deterministic_mapping_basic(headline, severity_input, is_disruption, expected_key):
    res1 = _map_fast_params(headline, severity=severity_input, is_disruption=is_disruption)
    res2 = _map_fast_params(headline, severity=severity_input, is_disruption=is_disruption)
    assert res1 == res2
    exp_sev, exp_dur = SEVERITY_RUBRIC[expected_key]
    assert res1["severity_pct"] == exp_sev
    assert res1["duration_days"] == exp_dur

def test_overrides_take_precedence():
    headline = "Any headline"
    res = _map_fast_params(
        headline,
        severity="HIGH",
        is_disruption=True,
        severity_pct_override=55,
        duration_days_override=30,
    )
    assert res["severity_pct"] == 55
    assert res["duration_days"] == 30
    assert res["params_source"] == "user_override"
