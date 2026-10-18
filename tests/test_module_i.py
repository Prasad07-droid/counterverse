# tests/test_module_i.py
"""Tests for the decision support report generation module and pipeline endpoint."""

import re
import pytest
from src.module_i_report import (
    build_report_data,
    render_pdf_bytes,
    generate_report,
    GENERIC_DISRUPTION_NOTE,
    DISAGREEMENT_TEMPLATE,
    CONFIDENCE_LIMITS_TEXT,
    FOOTER_TEXT,
)


@pytest.fixture
def sample_signal():
    """Minimal signal structure expected by generate_report for backwards compatibility."""
    return {
        "event_type": "supply_disruption",
        "canonical_component": "semiconductors",
        "canonical_region": "global",
        "severity_pct": 30,
        "duration_days": 10,
        "risk_score": 0.6,
        "breakdown": {"severity": 30, "duration": 10},
    }


def test_generate_report_contains_keys(sample_signal):
    """Existing test: ensures backwards compatibility of returned dictionary keys."""
    report = generate_report(sample_signal)
    expected_keys = {
        "explanation",
        "estimated_impact",
        "recommended_action",
        "risk_score",
        "risk_breakdown",
        "mc_stats",
        "pcar",
        "report_url",
    }
    assert expected_keys.issubset(report.keys())
    assert isinstance(report["explanation"], str)
    assert isinstance(report["risk_score"], (float, int))
    assert isinstance(report["mc_stats"], dict)
    assert isinstance(report["pcar"], dict)


def test_a_high_band_monitor_disagreement_sentence():
    """(a) HIGH band + cost-adjusted Monitor => disagreement sentence present;

    band HIGH never appears with 'Monitor' without that explanation sentence.
    """
    # Risk 0.88 (HIGH >= 0.60), but low PCaR mean (10 Cr) makes Monitor win argmax net benefit
    payload = {
        "headline": "China restricts exports of critical elements",
        "target_oem": "Maruti Suzuki",
        "risk_score": 0.88,
        "risk_result": {
            "risk_score": 0.88,
            "risk_level": "HIGH",
            "recommended_action": "Replace Supplier / Qualify Dual-Sourcing Immediately (CSCO Directive)",
        },
        "mc_result": {"mean_drop": 25.0, "p95_drop": 38.0},
        "pcar_metrics": {
            "mean_loss_crore": 10.0,
            "pcar_95_crore": 25.0,
            "effective_base_crore": 100.0,
        },
    }
    data = build_report_data(payload)
    assert data["risk"]["risk_band"] == "HIGH"
    assert data["decision"]["cost_adjusted_action"] == "Monitor & Maintain"

    # Must contain disagreement sentence
    disagreement = data["decision"]["disagreement_sentence"]
    assert disagreement is not None
    assert "The risk band indicates Replace Supplier / Qualify Dual-Sourcing Immediately" in disagreement
    assert "The cost-adjusted comparison selects Monitor & Maintain" in disagreement
    assert "versus -38.00 Cr for Qualify Dual Source" in disagreement

    pdf_bytes = render_pdf_bytes(data)
    pdf_text = pdf_bytes.decode("ascii")

    # Assert that if HIGH band and Monitor are both present, the explanation sentence is also present
    assert "Band Directive: Replace Supplier / Qualify Dual-Sourcing Immediately" in pdf_text
    assert "Cost-Adjusted Action: Monitor & Maintain" in pdf_text
    assert "The risk band indicates" in pdf_text
    assert "Costs and reductions are illustrative model assumptions." in pdf_text


def test_b_long_headline_wrapped_not_truncated():
    """(b) 200-character headline: every word appears in the PDF text stream,

    and no line exceeds the page width limit.
    """
    long_headline = (
        "China restricts critical raw gallium and germanium exports citing national "
        "security concerns sparking extensive automotive semiconductor shortage and "
        "extended production downtime across global car assembly facilities"
    )
    assert len(long_headline) >= 200

    payload = {
        "headline": long_headline,
        "risk_score": 0.75,
        "target_oem": "Tata Motors",
    }
    data = build_report_data(payload)
    pdf_bytes = render_pdf_bytes(data)
    pdf_text = pdf_bytes.decode("ascii")

    # Every single word must be present in the text stream
    words = long_headline.split()
    for w in words:
        assert w in pdf_text, f"Word '{w}' was truncated or missing from PDF stream"

    # Verify wrapped lines do not exceed 82 characters
    from src.module_i_report import _wrap_text
    wrapped = _wrap_text(long_headline, max_chars=78)
    for line in wrapped:
        assert len(line) <= 82


def test_c_numbers_match_inputs():
    """(c) every number in sections 1, 5, 6, 8 equals the input value."""
    payload = {
        "headline": "Semiconductor fire in fab",
        "target_oem": "Mahindra",
        "engine_used": "fast",
        "risk_score": 0.72,
        "risk_result": {
            "risk_score": 0.72,
            "risk_level": "HIGH",
            "recommended_action": "Replace Supplier / Qualify Dual-Sourcing Immediately (CSCO Directive)",
            "breakdown": {
                "exposure_breadth": {"value": 0.65},
                "dependency_ratio": {"value": 0.42},
                "downstream_criticality": {"value": 0.85},
                "tier1_centrality": {"value": 0.50},
                "exposure_depth": {"value": 0.75},
            },
        },
        "mc_result": {
            "mean_drop": 21.5,
            "median_drop": 19.8,
            "p95_drop": 34.2,
            "p99_drop": 42.1,
            "n_samples": 10000,
            "seed": 42,
            "distribution_source": "beta_distribution",
        },
        "pcar_metrics": {
            "effective_base_crore": 1250.75,
            "mean_loss_crore": 185.50,
            "median_loss_crore": 160.25,
            "pcar_95_crore": 412.35,
            "pcar_99_crore": 580.90,
            "worst_case_loss_crore": 820.00,
            "extra_procurement_cost_mean_crore": 98.40,
        },
    }
    data = build_report_data(payload)

    # Section 1 & 5
    assert data["risk"]["risk_score"] == 0.72
    assert data["mc"]["mean_drop"] == 21.5
    assert data["mc"]["p95_drop"] == 34.2
    assert data["pcar"]["pcar_95_crore"] == 412.35

    # Section 6
    assert data["pcar"]["effective_base_crore"] == 1250.75
    assert data["pcar"]["mean_loss_crore"] == 185.50
    assert data["pcar"]["median_loss_crore"] == 160.25
    assert data["pcar"]["pcar_99_crore"] == 580.90
    assert data["pcar"]["worst_case_loss_crore"] == 820.00
    assert data["pcar"]["extra_procurement_cost_crore"] == 98.40

    # Section 8 options
    ranked = data["decision"]["options_ranked"]
    dual = next(opt for opt in ranked if opt["action"] == "Qualify Dual Source")
    # avoided loss = 185.50 * 0.70 = 129.85 Cr; net benefit = 129.85 - 45 = 84.85 Cr
    assert dual["avoided_loss_crore"] == 129.85
    assert dual["net_benefit_crore"] == 84.85

    pdf_bytes = render_pdf_bytes(data)
    pdf_text = pdf_bytes.decode("ascii")
    assert "412.35" in pdf_text
    assert "185.50" in pdf_text
    assert "1250.75" in pdf_text
    assert "84.85" in pdf_text


def test_d_missing_pcar_prints_not_available():
    """(d) missing PCaR input prints 'Not available', never a number or 0.00."""
    payload = {
        "headline": "Unknown raw disruption",
        "target_oem": "Hyundai India",
        "pcar_metrics": None,
    }
    data = build_report_data(payload)
    assert data["pcar"]["has_real_pcar"] is False
    assert data["pcar"]["mean_loss_crore"] is None
    assert data["pcar"]["pcar_95_crore"] is None

    pdf_bytes = render_pdf_bytes(data)
    pdf_text = pdf_bytes.decode("ascii")
    assert "Not available" in pdf_text
    # Should not show fake 0.00 Cr for PCaR P95 Loss
    assert "PCaR P95 Loss                     0.00" not in pdf_text


def test_e_no_forbidden_phrases_and_strict_ascii():
    """(e) no forbidden phrases, no non-ASCII bytes in the text stream,

    no Hinglish marker words (hai, karo, nahi, kya, aur, liye, matlab).
    """
    payload = {
        "headline": "Global chip fab equipment delay halts microcontrollers",
        "target_oem": "Maruti Suzuki",
        "risk_score": 0.65,
        "pcar_metrics": {
            "mean_loss_crore": 120.0,
            "pcar_95_crore": 260.0,
            "effective_base_crore": 900.0,
        },
    }
    data = build_report_data(payload)
    pdf_bytes = render_pdf_bytes(data)

    # 1. Strict ASCII encoding check
    pdf_text = pdf_bytes.decode("ascii")

    # 2. Forbidden phrases
    forbidden_phrases = [
        "zero hallucination",
        "real-time",
        "validated",
        "accurate forecast",
        "guaranteed",
        "94.7",
        "Causal AI",
        "Confidential",
    ]
    for fp in forbidden_phrases:
        assert fp.lower() not in pdf_text.lower(), f"Forbidden phrase '{fp}' found in PDF output"

    # 3. Hinglish marker words
    hinglish_words = ["hai", "karo", "nahi", "kya", "aur", "liye", "matlab"]
    for hw in hinglish_words:
        assert not re.search(r"\b" + re.escape(hw) + r"\b", pdf_text, re.IGNORECASE), f"Hinglish word '{hw}' found in PDF output"


def test_f_same_input_twice_identical_text():
    """(f) same input twice gives identical text except timestamp."""
    payload = {
        "headline": "TSMC packaging unit flood in Tainan",
        "target_oem": "Tata Motors",
        "risk_score": 0.55,
        "pcar_metrics": {
            "mean_loss_crore": 80.0,
            "pcar_95_crore": 190.0,
            "effective_base_crore": 600.0,
        },
    }
    data1 = build_report_data(payload)
    data2 = build_report_data(payload)

    # Freeze timestamp for determinism comparison
    data1["metadata"]["timestamp_utc"] = "2026-10-07 12:00:00 UTC"
    data2["metadata"]["timestamp_utc"] = "2026-10-07 12:00:00 UTC"

    pdf1 = render_pdf_bytes(data1)
    pdf2 = render_pdf_bytes(data2)

    assert pdf1 == pdf2


def test_g_generic_event_type_triggers_review_note():
    """(g) generic event type triggers the review note."""
    # 1. Generic disruption type
    payload_generic = {
        "headline": "Generic unknown disruption in logistics",
        "signal": {"disruption_type": "Generic Disruption"},
    }
    data_gen = build_report_data(payload_generic)
    assert data_gen["signal"]["generic_note"] == GENERIC_DISRUPTION_NOTE
    pdf_gen = render_pdf_bytes(data_gen).decode("ascii")
    assert GENERIC_DISRUPTION_NOTE in pdf_gen

    # 2. Specific disruption type
    payload_specific = {
        "headline": "Export restriction on critical minerals",
        "signal": {"disruption_type": "Trade Policy", "event_type": "Export ban/restriction"},
    }
    data_spec = build_report_data(payload_specific)
    assert data_spec["signal"]["generic_note"] is None


def test_h_pdf_sanity_page_count():
    """(h) PDF sanity: starts with %PDF-1.4, ends with %%EOF,

    /Type /Page count equals the 'of N' in the footer.
    """
    payload = {
        "headline": "Earthquake in Kyushu halts wafer plant",
        "target_oem": "Maruti Suzuki",
    }
    data = build_report_data(payload)
    pdf_bytes = render_pdf_bytes(data)

    assert pdf_bytes.startswith(b"%PDF-1.4")
    assert pdf_bytes.strip().endswith(b"%%EOF")

    pdf_text = pdf_bytes.decode("ascii")
    # Verify exactly 3 page objects
    page_matches = re.findall(r"/Type\s*/Page\b", pdf_text)
    # /Type /Pages is the catalog kid container; /Type /Page is the individual page
    # In our objs, /Type /Page appears for 3 pages (plus /Pages for root)
    assert len(page_matches) == 3

    # Check footer page markers
    assert "Page 1 of 3" in pdf_text
    assert "Page 2 of 3" in pdf_text
    assert "Page 3 of 3" in pdf_text


def test_i_route_ignores_client_supplied_pcar_and_drop():
    """(i) the route ignores client-supplied pcar_cr / p95_drop / mean_drop."""
    from fastapi.testclient import TestClient
    from api.main import app

    client = TestClient(app)
    # Client posts fake numbers that should be ignored by the real backend pipeline
    client_payload = {
        "headline": "China restricts gallium and germanium exports citing national security",
        "oem": "Maruti Suzuki",
        "engine": "fast",
        "pcar_cr": 999999.0,
        "p95_drop": 99.9,
        "mean_drop": 88.8,
    }

    response = client.post("/api/v1/generate-report", json=client_payload)
    assert response.status_code == 200
    res_json = response.json()

    # The server-side pipeline computes real numbers, never echoing 999999.0 or 99.9
    assert res_json["risk_score"] > 0.0
    mc_stats = res_json["mc_stats"]
    assert mc_stats["mean_drop"] != 88.8
    assert mc_stats["p95_drop"] != 99.9
    assert res_json["report_url"].startswith("/static/reports/")
