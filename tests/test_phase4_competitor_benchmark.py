# -*- coding: utf-8 -*-
"""
Tests for Phase 4: Resilinc Functional Benchmark Document
=========================================================
Covers:
  - docs/competitor_benchmark_resilinc.md existence and required structure
  - Verification of 11 required functional capability rows
  - Claims audit section (AI agents, 100+ languages, India, pricing, Monte Carlo)
  - Deliberately different design choices section
  - Product-category conceptual diagram
  - Viva defensible wording
"""

from pathlib import Path


def test_competitor_benchmark_file_exists():
    """Verify that docs/competitor_benchmark_resilinc.md exists and is non-empty."""
    doc_path = Path(__file__).resolve().parents[1] / "docs" / "competitor_benchmark_resilinc.md"
    assert doc_path.exists(), "docs/competitor_benchmark_resilinc.md missing"
    content = doc_path.read_text(encoding="utf-8")
    assert len(content) > 1000


def test_competitor_benchmark_table_capabilities():
    """Verify that all 11 required functional capabilities are analyzed in the table."""
    doc_path = Path(__file__).resolve().parents[1] / "docs" / "competitor_benchmark_resilinc.md"
    content = doc_path.read_text(encoding="utf-8")

    required_capabilities = [
        "Event / News Monitoring",
        "Multi-Tier Supplier / Site Mapping",
        "Event-to-Exposure Linking",
        "Risk Scoring & Prioritization",
        "Financial / Impact Analysis",
        "Alerts & Response Workflow",
        "AI / Agentic Features",
        "Language Coverage",
        "India / Regional Automotive Focus",
        "Pricing & Packaging",
        "Stochastic Simulation / Monte Carlo",
    ]

    for cap in required_capabilities:
        assert cap in content, f"Missing capability row: {cap}"


def test_claims_audit_section():
    """Verify that the 5 claims are audited with evidence and citations."""
    doc_path = Path(__file__).resolve().parents[1] / "docs" / "competitor_benchmark_resilinc.md"
    content = doc_path.read_text(encoding="utf-8")

    assert "Audit of Claims Given for Report Verification" in content
    assert "AI Agents" in content and "VERIFIED" in content
    assert "100+ languages" in content and "VERIFIED" in content
    assert "India coverage" in content and "VERIFIED" in content
    assert "Pricing" in content
    assert "Monte Carlo" in content and "NOT VERIFIED" in content


def test_deliberate_differences_and_viva_phrasing():
    """Verify that Causal AI and Small Language Models for Supply Chain Disruption Forecasting and Procurement Cost at Risk Estimation for Indian Automotive Component Sourcing's deliberate differences and viva phrasing are included."""
    doc_path = Path(__file__).resolve().parents[1] / "docs" / "competitor_benchmark_resilinc.md"
    content = doc_path.read_text(encoding="utf-8")

    assert "Where Causal AI and Small Language Models for Supply Chain Disruption Forecasting and Procurement Cost at Risk Estimation for Indian Automotive Component Sourcing is Deliberately Different" in content
    assert "Narrow Scope" in content
    assert "Open, Audit-Transparent Formulas" in content or "Open Formula" in content
    assert "Deterministic AI Safety Separation" in content
    assert "Stochastic Stress Testing with Reproducible Seeds" in content or "Reproducible Seed" in content
    assert "Typical Commercial Product-Category Conceptual Architecture" in content
    assert "Defensible Wording for External Viva & Report" in content
    assert "closest commercial analogue" in content
