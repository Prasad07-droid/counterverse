# -*- coding: utf-8 -*-
"""
Tests for Phase 2: Honest Status for Data Sources
==================================================
Covers:
  - GDELT HTTP 429 backoff and fallback to RSS
  - GDELT and RSS timeout fallback to SQLite cache
  - SQLite headline cache deduplication
  - Twitter explicit 'not_configured' status when credentials missing
  - GET /api/v1/headlines endpoint schema and provenance fields
  - data_provenance block in /api/v1/calculate-pcar and /api/v1/calculate-custom-bom
  - Direct PCaR module functions data_provenance integration
"""

import os
import urllib.error
from unittest.mock import patch, MagicMock
import numpy as np
import pytest
from fastapi.testclient import TestClient

from api.main import app
from src.data_sources import (
    fetch_headlines_resilient,
    fetch_live_gdelt_headlines,
    fetch_rss_headlines,
    cache_headlines,
    load_cached_headlines,
)
from src.module_a_ingest import _fetch_twitter
from src.module_e_pcar import (
    calculate_pcar,
    calculate_pcar_by_company,
    calculate_pcar_custom_bom,
    COMTRADE_DATA_PROVENANCE,
)


# ── Fixtures ──

@pytest.fixture
def client():
    return TestClient(app)


# ── 1. GDELT 429 Backoff and RSS Fallback ──

def test_gdelt_429_backoff_and_fallback_to_rss(monkeypatch):
    """When GDELT returns HTTP 429, fetch_headlines_resilient falls back to RSS."""
    # Speed up backoff by mocking sleep
    monkeypatch.setattr("time.sleep", lambda s: None)

    # Mock GDELT urlopen to raise HTTPError 429
    def mock_gdelt_urlopen(*args, **kwargs):
        raise urllib.error.HTTPError(
            url="https://api.gdeltproject.org",
            code=429,
            msg="Too Many Requests",
            hdrs={},
            fp=None,
        )

    # Mock RSS to return live RSS articles
    rss_mock_articles = [
        {
            "title": "Automakers face critical chip bottleneck in semiconductor supply",
            "url": "https://news.google.com/articles/1",
            "seendate": "20261018",
            "domain": "news.google.com",
            "source": "Google News RSS",
            "provenance_type": "live_rss_feed",
            "is_illustrative": False,
        }
    ]

    with patch("urllib.request.urlopen", side_effect=mock_gdelt_urlopen):
        with patch("src.data_sources.fetch_rss_headlines", return_value={
            "success": True,
            "data_vintage": "LIVE RSS (UTC: 2026-10-18 12:00:00Z)",
            "fetch_timestamp_utc": "2026-10-18 12:00:00Z",
            "citation": "Google News RSS Feed",
            "articles": rss_mock_articles,
            "fallback_tier": "RSS_LIVE",
            "is_stale": False,
            "staleness_warning": None,
        }):
            res = fetch_headlines_resilient(max_records=5)

    assert res["success"] is True
    assert res["fallback_tier"] == "RSS_LIVE"
    assert len(res["articles"]) > 0
    assert res["articles"][0]["provenance_type"] == "live_rss_feed"


# ── 2. Timeout Fallback to SQLite Cache ──

def test_timeout_fallback_to_sqlite(monkeypatch):
    """When GDELT and RSS timeout, fetch_headlines_resilient serves from SQLite cache."""
    # Pre-seed cache with test articles
    test_articles = [
        {
            "title": "Unique Cache Test Headline 2026",
            "url": "https://example.com/chip-news",
            "seendate": "20261018",
            "domain": "example.com",
            "source": "test_feed",
            "provenance_type": "cached",
            "is_illustrative": False,
        }
    ]
    cache_headlines(test_articles)

    # Force GDELT and RSS to fail (simulating network timeout)
    with patch("src.data_sources.fetch_live_gdelt_headlines", return_value={"success": False, "articles": []}):
        with patch("src.data_sources.fetch_rss_headlines", return_value={"success": False, "articles": []}):
            res = fetch_headlines_resilient(max_records=5)

    assert res["success"] is True
    assert res["fallback_tier"] == "SQLITE_CACHE"
    assert any("Unique Cache Test Headline" in a["title"] for a in res["articles"])
    assert res["staleness_warning"] is not None


# ── 3. SQLite Cache Headline Deduplication ──

def test_sqlite_cache_deduplication():
    """Duplicate headlines must be ignored by the SQLite cache."""
    duplicate_articles = [
        {
            "title": "Duplicate Gallium Supply Crisis Headline",
            "url": "https://example.com/dup1",
            "seendate": "20261018",
            "domain": "example.com",
            "source": "feed1",
            "provenance_type": "live_gdelt_feed",
            "is_illustrative": False,
        },
        {
            "title": "Duplicate Gallium Supply Crisis Headline",
            "url": "https://example.com/dup2",
            "seendate": "20261018",
            "domain": "example.com",
            "source": "feed2",
            "provenance_type": "live_gdelt_feed",
            "is_illustrative": False,
        },
    ]

    inserted_first = cache_headlines([duplicate_articles[0]])
    inserted_second = cache_headlines([duplicate_articles[1]])

    # First insert may be 1 or 0 (if already exists from prior test), but second insert must be 0
    assert inserted_second == 0


# ── 4. Twitter Explicit not_configured Status ──

def test_twitter_not_configured_when_no_token(monkeypatch):
    """When COUNTERVERSE_TWITTER_BEARER_TOKEN is absent, Twitter returns explicit not_configured."""
    monkeypatch.delenv("COUNTERVERSE_TWITTER_BEARER_TOKEN", raising=False)

    tw = _fetch_twitter()
    assert isinstance(tw, dict)
    assert tw["status"] == "not_configured"
    assert tw["articles"] == []
    assert "not configured" in tw["message"].lower()


# ── 5. GET /api/v1/headlines Endpoint Schema & Status ──

def test_get_headlines_endpoint_schema(client):
    """GET /api/v1/headlines returns required fields, fallback_tier, and sources_status."""
    resp = client.get("/api/v1/headlines?max_records=5")
    assert resp.status_code == 200

    data = resp.json()
    assert "fallback_tier" in data
    assert data["fallback_tier"] in ("GDELT_LIVE", "RSS_LIVE", "SQLITE_CACHE", "STATIC_FALLBACK")
    assert "data_vintage" in data
    assert "is_stale" in data
    assert "total_headlines" in data
    assert "articles" in data
    assert isinstance(data["articles"], list)

    assert "sources_status" in data
    sources = data["sources_status"]
    assert "gdelt" in sources
    assert "rss" in sources
    assert "sqlite" in sources
    assert "twitter" in sources

    # Without token, Twitter status must be explicit not_configured
    assert sources["twitter"]["status"] in ("not_configured", "active", "error")
    if not os.getenv("COUNTERVERSE_TWITTER_BEARER_TOKEN"):
        assert sources["twitter"]["status"] == "not_configured"


# ── 6. Data Provenance in /calculate-pcar ──

def test_api_calculate_pcar_has_data_provenance(client):
    """POST /api/v1/calculate-pcar must include data_provenance block."""
    resp = client.post(
        "/api/v1/calculate-pcar",
        json={
            "company": "Maruti Suzuki",
            "risk_score": 0.65,
            "mc_samples": 500,
        },
    )
    assert resp.status_code == 200
    data = resp.json()

    assert "data_provenance" in data
    prov = data["data_provenance"]
    assert prov is not None
    assert prov["reporter"] == "India (699)"
    assert prov["hs_code"] == "8542"
    assert prov["storage_type"] == "static_cache"
    assert "disclaimer" in prov
    assert "Comtrade" in prov["disclaimer"]


# ── 7. Data Provenance in /calculate-custom-bom ──

def test_api_calculate_custom_bom_has_data_provenance(client):
    """POST /api/v1/calculate-custom-bom must include data_provenance block."""
    resp = client.post(
        "/api/v1/calculate-custom-bom",
        json={
            "company_name": "Test OEM Corp",
            "components": [
                {
                    "component_name": "Engine Control Unit",
                    "hs_code": "8542",
                    "annual_spend_crore": 250.0,
                }
            ],
            "risk_score": 0.5,
            "mc_samples": 500,
        },
    )
    assert resp.status_code == 200
    data = resp.json()

    assert "data_provenance" in data
    prov = data["data_provenance"]
    assert prov is not None
    assert prov["reporter"] == "India (699)"
    assert "disclaimer" in prov


# ── 8. Direct PCaR Functions Include COMTRADE_DATA_PROVENANCE ──

def test_module_e_pcar_direct_provenance():
    """Direct calls to PCaR functions return COMTRADE_DATA_PROVENANCE."""
    samples = np.array([5.0, 10.0, 15.0])

    # Macro PCaR
    macro = calculate_pcar(samples, company_name="Entire Indian Automotive Industry", random_seed=42)
    assert "data_provenance" in macro
    assert macro["data_provenance"]["reporter"] == "India (699)"
    assert macro["data_provenance"]["hs_code"] == "8542"

    # Company PCaR
    comp = calculate_pcar_by_company("Maruti Suzuki", macro)
    assert "data_provenance" in comp
    assert comp["data_provenance"]["reporter"] == "India (699)"

    # Custom BOM PCaR
    bom = calculate_pcar_custom_bom(
        samples,
        bom_components=[{"component_name": "MCU", "hs_code": "8542", "annual_spend_crore": 100.0}],
        company_name="Custom OEM",
        random_seed=42,
    )
    assert "data_provenance" in bom
    assert bom["data_provenance"]["reporter"] == "India (699)"
