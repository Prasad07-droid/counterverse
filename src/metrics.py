# -*- coding: utf-8 -*-
# Prometheus metrics + Slack/Teams alerting for CounterVerse
import os
import logging
import time
from contextlib import contextmanager

logger = logging.getLogger(__name__)

try:
    from prometheus_client import Counter, Histogram, Gauge

    REQUEST_COUNT = Counter(
        "counterverse_requests_total",
        "Total API requests handled",
        ["endpoint", "status"],
    )
    PIPELINE_LATENCY = Histogram(
        "counterverse_pipeline_latency_seconds",
        "End-to-end pipeline latency in seconds",
        ["endpoint"],
        buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    )
    RISK_SCORE_GAUGE = Gauge("counterverse_last_risk_score", "Last risk score")
    PCAR_GAUGE = Gauge("counterverse_last_pcar_95_crore", "Last PCaR 95th-pct (Crore)")
    PROMETHEUS_AVAILABLE = True

    @contextmanager
    def track_latency(endpoint: str):
        start = time.perf_counter()
        status = "success"
        try:
            yield
        except Exception:
            status = "error"
            raise
        finally:
            PIPELINE_LATENCY.labels(endpoint=endpoint).observe(time.perf_counter() - start)
            REQUEST_COUNT.labels(endpoint=endpoint, status=status).inc()

except ImportError:
    PROMETHEUS_AVAILABLE = False
    REQUEST_COUNT = PIPELINE_LATENCY = RISK_SCORE_GAUGE = PCAR_GAUGE = None

    @contextmanager
    def track_latency(endpoint: str):
        yield

    logger.debug("prometheus_client not installed; metrics collection disabled.")


_SLACK_WEBHOOK = os.getenv("COUNTERVERSE_SLACK_WEBHOOK_URL")
_TEAMS_WEBHOOK = os.getenv("COUNTERVERSE_TEAMS_WEBHOOK_URL")


def alert_slack(message: str, level: str = "info") -> bool:
    if not _SLACK_WEBHOOK:
        return False
    tag = {"info": "INFO", "warning": "WARN", "critical": "CRIT"}.get(level, "ALERT")
    try:
        import requests
        resp = requests.post(
            _SLACK_WEBHOOK,
            json={"text": "[" + tag + "] CounterVerse: " + message},
            timeout=5,
        )
        return resp.status_code == 200
    except Exception as exc:
        logger.warning("Slack alert failed: %s", exc)
        return False


def alert_teams(message: str, level: str = "info") -> bool:
    if not _TEAMS_WEBHOOK:
        return False
    colors = {"info": "0076D7", "warning": "FFA500", "critical": "FF0000"}
    payload = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": colors.get(level, "0076D7"),
        "summary": "CounterVerse Alert",
        "sections": [{"activityTitle": "CounterVerse [" + level.upper() + "]", "text": message}],
    }
    try:
        import requests
        resp = requests.post(_TEAMS_WEBHOOK, json=payload, timeout=5)
        return resp.status_code == 200
    except Exception as exc:
        logger.warning("Teams alert failed: %s", exc)
        return False
