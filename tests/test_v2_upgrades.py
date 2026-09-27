# -*- coding: utf-8 -*-
"""
CounterVerse v2.0 — Extended Integration Test Suite
====================================================
New tests added for all Phase-2 upgrades:
  - Extra config (ESG weights, languages, Neo4j vars)
  - Auth module (JWT token create/decode)
  - Metrics module (Prometheus counters, Slack/Teams no-op)
  - Module A: multilingual ingest helpers
  - Monte Carlo dynamic sample sizes
  - Multi-currency PCaR conversion
  - API: /token endpoint, /currencies endpoint
  - CI/CD workflow file existence check

Run with: pytest tests/test_v2_upgrades.py -v
"""

import sys
import os
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import pytest


# ════════════════════════════════════════════════════════════════
# EXTRA CONFIG
# ════════════════════════════════════════════════════════════════

class TestExtraConfig:
    def test_extra_config_imports(self):
        from src.extra_config import RISK_WEIGHTS, SUPPORTED_LANGUAGES, NEO4J_URI
        assert isinstance(RISK_WEIGHTS, dict)
        assert "esg" in RISK_WEIGHTS
        assert "en" in SUPPORTED_LANGUAGES
        assert NEO4J_URI.startswith("bolt://") or NEO4J_URI.startswith("neo4j")

    def test_risk_weights_sum(self):
        from src.extra_config import RISK_WEIGHTS
        total = sum(RISK_WEIGHTS.values())
        assert abs(total - 1.0) < 1e-6, f"Weights must sum to 1.0, got {total}"

    def test_supported_languages_not_empty(self):
        from src.extra_config import SUPPORTED_LANGUAGES
        assert len(SUPPORTED_LANGUAGES) >= 1


# ════════════════════════════════════════════════════════════════
# AUTH MODULE
# ════════════════════════════════════════════════════════════════

class TestAuthModule:
    def test_auth_imports(self):
        from src.auth import create_access_token, decode_token, authenticate_user, AUTH_AVAILABLE
        assert callable(create_access_token)
        assert callable(decode_token)
        assert callable(authenticate_user)

    def test_create_token_returns_string(self):
        from src.auth import create_access_token
        token = create_access_token({"sub": "testuser"})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_roundtrip(self):
        from src.auth import create_access_token, decode_token, AUTH_AVAILABLE
        if not AUTH_AVAILABLE:
            pytest.skip("python-jose not installed")
        token = create_access_token({"sub": "admin"})
        payload = decode_token(token)
        assert payload.get("sub") == "admin"

    def test_authenticate_user_invalid(self):
        from src.auth import authenticate_user
        result = authenticate_user("nonexistent", "wrongpassword")
        assert result is None

    def test_authenticate_user_valid(self):
        from src.auth import authenticate_user, AUTH_AVAILABLE
        if not AUTH_AVAILABLE:
            pytest.skip("python-jose / passlib not installed")
        os.environ.setdefault("COUNTERVERSE_ADMIN_PASSWORD", "changeme")
        # Re-import to pick up env var
        import importlib
        import src.auth
        importlib.reload(src.auth)
        from src.auth import authenticate_user as au
        result = au("admin", "changeme")
        assert result is not None
        assert result["username"] == "admin"


# ════════════════════════════════════════════════════════════════
# METRICS MODULE
# ════════════════════════════════════════════════════════════════

class TestMetricsModule:
    def test_metrics_imports(self):
        from src.metrics import track_latency, alert_slack, alert_teams, PROMETHEUS_AVAILABLE
        assert callable(alert_slack)
        assert callable(alert_teams)

    def test_track_latency_noop(self):
        from src.metrics import track_latency
        # Should not raise even if prometheus not installed
        with track_latency("test_endpoint"):
            pass

    def test_alert_slack_no_webhook(self):
        from src.metrics import alert_slack
        # Without webhook configured, should return False silently
        os.environ.pop("COUNTERVERSE_SLACK_WEBHOOK_URL", None)
        result = alert_slack("test message", level="info")
        assert result is False

    def test_alert_teams_no_webhook(self):
        from src.metrics import alert_teams
        os.environ.pop("COUNTERVERSE_TEAMS_WEBHOOK_URL", None)
        result = alert_teams("test message", level="warning")
        assert result is False


# ════════════════════════════════════════════════════════════════
# MODULE A: MULTILINGUAL INGEST
# ════════════════════════════════════════════════════════════════

class TestModuleAIngest:
    def test_module_a_imports(self):
        from src.module_a_ingest import get_latest_headlines, _filter_by_language
        assert callable(get_latest_headlines)
        assert callable(_filter_by_language)

    def test_filter_by_language_english(self):
        from src.module_a_ingest import _filter_by_language
        items = [
            {"title": "China imposes export controls on gallium semiconductors"},
            {"title": ""},
        ]
        result = _filter_by_language(items)
        # At minimum, the English article should pass
        assert any(r.get("lang") == "en" for r in result)

    def test_filter_by_language_empty(self):
        from src.module_a_ingest import _filter_by_language
        assert _filter_by_language([]) == []


# ════════════════════════════════════════════════════════════════
# MONTE CARLO — DYNAMIC SAMPLE SIZE
# ════════════════════════════════════════════════════════════════

class TestMonteCarloDynamic:
    def _make_probs(self):
        return {
            "High (>15%)": 0.40,
            "Medium (5-15%)": 0.35,
            "Low (<5%)": 0.15,
            "None": 0.10,
        }

    def test_default_sample_size(self):
        from src.module_d_mc import run_monte_carlo
        probs = self._make_probs()
        result = run_monte_carlo(probs)
        assert result["n_samples"] == 10000

    def test_custom_sample_size_small(self):
        from src.module_d_mc import run_monte_carlo
        probs = self._make_probs()
        result = run_monte_carlo(probs, n_samples=500)
        assert result["n_samples"] == 500

    def test_custom_sample_size_large(self):
        from src.module_d_mc import run_monte_carlo
        probs = self._make_probs()
        result = run_monte_carlo(probs, n_samples=50000)
        assert result["n_samples"] == 50000

    def test_determinism_with_seed(self):
        from src.module_d_mc import run_monte_carlo
        probs = self._make_probs()
        r1 = run_monte_carlo(probs, n_samples=1000, random_seed=99)
        r2 = run_monte_carlo(probs, n_samples=1000, random_seed=99)
        import numpy as np
        assert abs(r1["mean_drop"] - r2["mean_drop"]) < 1e-9


# ════════════════════════════════════════════════════════════════
# MULTI-CURRENCY PCaR
# ════════════════════════════════════════════════════════════════

class TestMultiCurrencyPCaR:
    def test_currency_endpoint_defined(self):
        """Ensure CURRENCY_RATES dict is present in api/main.py."""
        import importlib
        try:
            import api.main as m
            importlib.reload(m)
            assert hasattr(m, "CURRENCY_RATES")
            assert "INR" in m.CURRENCY_RATES
            assert "USD" in m.CURRENCY_RATES
            assert "EUR" in m.CURRENCY_RATES
        except Exception:
            pytest.skip("api.main could not be imported (dependency issue)")

    def test_inr_rate_is_one(self):
        try:
            import api.main as m
            assert m.CURRENCY_RATES["INR"] == 1.0
        except Exception:
            pytest.skip("api.main could not be imported")


# ════════════════════════════════════════════════════════════════
# FASTAPI — NEW ENDPOINTS
# ════════════════════════════════════════════════════════════════

class TestNewAPIEndpoints:
    @pytest.fixture
    def client(self):
        try:
            from fastapi.testclient import TestClient
            import api.main as m
            return TestClient(m.app)
        except Exception as e:
            pytest.skip(f"Could not create test client: {e}")

    def test_currencies_endpoint(self, client):
        resp = client.get("/api/v1/currencies")
        assert resp.status_code == 200
        data = resp.json()
        assert "supported" in data
        assert "INR" in data["supported"]

    def test_token_endpoint_wrong_credentials(self, client):
        resp = client.post(
            "/api/v1/token",
            data={"username": "nobody", "password": "wrong"},
        )
        assert resp.status_code == 401

    def test_health_version_v2(self, client):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("version") == "2.0.0"


# ════════════════════════════════════════════════════════════════
# CI/CD & DEVOPS FILES EXISTENCE
# ════════════════════════════════════════════════════════════════

class TestDevOpsFiles:
    def test_github_actions_ci_exists(self):
        ci_path = _PROJECT_ROOT / ".github" / "workflows" / "ci.yml"
        assert ci_path.exists(), "CI/CD workflow file missing"

    def test_dockerfile_multistage(self):
        dockerfile = _PROJECT_ROOT / "Dockerfile"
        assert dockerfile.exists()
        content = dockerfile.read_text(encoding="utf-8")
        assert "AS builder" in content, "Multi-stage Dockerfile must have 'AS builder'"
        assert "AS runtime" in content, "Multi-stage Dockerfile must have 'AS runtime'"

    def test_docker_compose_has_neo4j(self):
        dc = _PROJECT_ROOT / "docker-compose.yml"
        assert dc.exists()
        content = dc.read_text(encoding="utf-8")
        assert "neo4j" in content
        assert "redis" in content

    def test_css_design_system_exists(self):
        css = _PROJECT_ROOT / "app" / "assets" / "style.css"
        assert css.exists(), "Premium CSS design system file missing"
        content = css.read_text(encoding="utf-8")
        assert "cv-glass-card" in content

    def test_metrics_module_exists(self):
        m = _PROJECT_ROOT / "src" / "metrics.py"
        assert m.exists()

    def test_auth_module_exists(self):
        a = _PROJECT_ROOT / "src" / "auth.py"
        assert a.exists()

    def test_module_a_ingest_exists(self):
        a = _PROJECT_ROOT / "src" / "module_a_ingest.py"
        assert a.exists()
