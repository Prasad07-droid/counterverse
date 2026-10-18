# -*- coding: utf-8 -*-
"""
CounterVerse FastAPI REST Backend
=================================
Provides headless access to the full CounterVerse pipeline for
enterprise integration, CI/CD, and automated supply chain monitoring.

Endpoints:
  POST /api/v1/analyze-headline  — Full pipeline: SLM → GraphRAG → Risk → Directive
  POST /api/v1/simulate-risk     — Monte Carlo simulation with custom parameters
  POST /api/v1/calculate-pcar    — PCaR for predefined OEM or custom BOM
  GET  /api/v1/health            — System status, GPU, graph integrity

Launch:
  uvicorn api.main:app --host 0.0.0.0 --port 8000
"""

import os
import json
import sys
import uuid
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

# ── Auth, metrics, rate-limiting ──
try:
    from src.auth import (
        create_access_token,
        authenticate_user,
        AUTH_AVAILABLE,
        oauth2_scheme,
        require_roles,
        require_officer,
        require_analyst,
        require_admin,
        require_authenticated,
        verify_security_configuration,
    )
except ImportError:
    AUTH_AVAILABLE = False
    oauth2_scheme = None
    def create_access_token(data, expires_delta=None): return "no-auth"
    def authenticate_user(u, p): return None
    def require_roles(*r): return lambda: None
    require_officer = lambda: None
    require_analyst = lambda: None
    require_admin = lambda: None
    require_authenticated = lambda: None
    def verify_security_configuration(): pass

try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    _limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
    _SLOWAPI_AVAILABLE = True
except ImportError:
    _limiter = None
    _SLOWAPI_AVAILABLE = False

try:
    from src.metrics import PROMETHEUS_AVAILABLE, RISK_SCORE_GAUGE, PCAR_GAUGE
    from prometheus_client import make_asgi_app as _make_metrics_app
except ImportError:
    PROMETHEUS_AVAILABLE = False
    RISK_SCORE_GAUGE = PCAR_GAUGE = None
    _make_metrics_app = None

# ── Path setup ──
_API_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _API_DIR.parent
for p in [str(_PROJECT_ROOT), str(_API_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# ── Project imports ──
from src.grounding_graph import (
    get_grounding_graph,
    get_graph_summary,
    ground_entities,
    verify_graph_integrity,
    _compute_graph_hash,
)
from src.module_c_causal import (
    simulate_causal_impact,
    calculate_deterministic_risk_score,
    compute_cost_adjusted_recommendation,
    RISK_THRESHOLD_HIGH,
    RISK_THRESHOLD_MEDIUM,
    classify_risk_band,
)
from src.module_i_report import generate_report
from src.module_d_mc import run_monte_carlo
from src.module_e_pcar import (
    calculate_pcar,
    calculate_pcar_by_company,
    calculate_pcar_custom_bom,
    OEM_PROFILES,
    SUPPORTED_OEM_COMPANIES,
    METRIC_VERSION,
    PCAR_ASSUMPTIONS,
)
from src.data_sources import (
    SOURCED_HS8542_BASELINE_CRORE,
    USD_INR_RATE,
    load_comtrade_data,
    sanitize_headline,
    fetch_headlines_resilient,
)
from src.module_a_ingest import _fetch_twitter

logger = logging.getLogger("counterverse.api")

# ── SLM availability check ──
SLM_AVAILABLE = False
_SLM_SKIP_REASON = "Not loaded"
try:
    import torch
    _HAS_GPU = torch.cuda.is_available()
except ImportError:
    _HAS_GPU = False

if _HAS_GPU:
    try:
        from src.module_b_slm import extract_signal, extract_signal_with_grounding
        SLM_AVAILABLE = True
        _SLM_SKIP_REASON = None
    except (ImportError, RuntimeError, OSError) as e:
        _SLM_SKIP_REASON = str(e)
else:
    _SLM_SKIP_REASON = "No CUDA GPU available"

# Import fast heuristic always
try:
    from src.module_b_slm import extract_signal_fast
except ImportError:
    extract_signal_fast = None


# ════════════════════════════════════════════════════════════════
# REQUEST / RESPONSE SCHEMAS
# ════════════════════════════════════════════════════════════════

class HeadlineRequest(BaseModel):
    """Request body for /analyze-headline."""
    headline: str = Field(..., min_length=5, max_length=500, description="News headline text")
    engine: str = Field(
        default="fast",
        description="Inference engine: 'fast' (rule-based heuristic) or 'slm' (Qwen2.5 GPU inference)"
    )
    company: str = Field(
        default="Maruti Suzuki",
        description="Target OEM for PCaR calculation"
    )
    mc_samples: int = Field(default=10000, ge=100, le=500000, description="Monte Carlo sample count")
    severity_pct_override: Optional[int] = Field(
        default=None,
        ge=0,
        le=100,
        description="Optional extracted severity-percent override; omitted preserves current behavior",
    )
    duration_days_override: Optional[int] = Field(
        default=None,
        ge=1,
        le=90,
        description="Optional extracted duration-days override; omitted preserves current behavior",
    )

class HeadlineResponse(BaseModel):
    """Response for /analyze-headline."""
    headline: str
    engine_used: str
    signal: Dict[str, Any]
    grounding: Dict[str, Any]
    risk_score: float
    risk_label: str
    csco_directive: str
    pcar_metrics: Dict[str, Any]
    pipeline_time_ms: float

class SimulateRequest(BaseModel):
    """Request body for /simulate-risk."""
    event_type: str = Field(default="supply_disruption", description="Disruption event type")
    severity: int = Field(default=3, ge=1, le=5, description="Severity level (1-5)")
    duration_days: int = Field(default=30, ge=1, le=365, description="Expected disruption duration")
    mc_samples: int = Field(default=10000, ge=100, le=500000, description="Monte Carlo draws")
    random_seed: Optional[int] = Field(default=42, description="Random seed for reproducibility")

class SimulateResponse(BaseModel):
    """Response for /simulate-risk."""
    risk_score: float
    risk_label: str
    probabilities: Dict[str, Any]
    mc_stats: Dict[str, float]
    simulation_config: Dict[str, Any]
    pipeline_time_ms: float

class PcarRequest(BaseModel):
    """Request body for /calculate-pcar."""
    company: str = Field(
        default="Maruti Suzuki",
        description="Target OEM or 'Entire Indian Automotive Industry' for aggregate"
    )
    risk_score: float = Field(default=0.65, ge=0.0, le=1.0, description="Input risk score")
    mc_samples: int = Field(default=10000, ge=100, le=500000, description="Monte Carlo draws")
    custom_baseline_crore: Optional[float] = Field(
        default=None,
        description="Custom BOM baseline in Crore INR (overrides UN Comtrade default)"
    )
    baseline_output_value_crore: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Optional output-value baseline in Crore INR; omitted means lost-output metrics are unavailable"
    )

class PcarResponse(BaseModel):
    """Response for /calculate-pcar."""
    company_name: str
    effective_base_crore: float
    mean_loss_crore: float
    pcar_95_crore: float
    pcar_99_crore: float
    worst_case_loss_crore: float
    extra_procurement_cost_mean_crore: float
    extra_procurement_cost_p95_crore: float
    extra_procurement_cost_p99_crore: float
    lost_output_value_mean_crore: Optional[float] = None
    lost_output_value_p95_crore: Optional[float] = None
    lost_output_value_p99_crore: Optional[float] = None
    lost_output_value_status: str
    market_share_pct: Optional[float] = None
    dependency_ratio_pct: Optional[float] = None
    data_provenance: Optional[Dict[str, Any]] = None
    metric_version: str = "2.0.0"
    assumptions: Optional[Dict[str, Any]] = None
    pipeline_time_ms: float

class BOMComponentItem(BaseModel):
    """Line item in a Custom Bill of Materials."""
    component_name: str = Field(..., description="Component / part name")
    hs_code: str = Field(default="8542", description="HS Code (e.g. 8542 for Semiconductors)")
    annual_spend_crore: float = Field(..., gt=0, description="Annual procurement spend in ₹ Crore")

class CustomBOMRequest(BaseModel):
    """Request body for /calculate-custom-bom."""
    company_name: str = Field(default="Custom Enterprise OEM", description="Company or division name")
    components: List[BOMComponentItem] = Field(..., min_length=1, description="List of BOM line items")
    risk_score: float = Field(default=0.65, ge=0.0, le=1.0, description="Input risk score")
    mc_samples: int = Field(default=10000, ge=100, le=500000, description="Monte Carlo draws")
    ground_against_graph: bool = Field(default=True, description="Verify components against the grounding graph")
    baseline_output_value_crore: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Optional output-value baseline in Crore INR"
    )

class CustomBOMResponse(BaseModel):
    """Response for /calculate-custom-bom."""
    company_name: str
    effective_base_crore: float
    component_count: int
    mean_loss_crore: float
    pcar_95_crore: float
    pcar_99_crore: float
    worst_case_loss_crore: float
    extra_procurement_cost_mean_crore: float
    extra_procurement_cost_p95_crore: float
    extra_procurement_cost_p99_crore: float
    lost_output_value_mean_crore: Optional[float] = None
    lost_output_value_p95_crore: Optional[float] = None
    lost_output_value_p99_crore: Optional[float] = None
    lost_output_value_status: str
    component_grounding: List[Dict[str, Any]]
    data_provenance: Optional[Dict[str, Any]] = None
    metric_version: str = "2.0.0"
    assumptions: Optional[Dict[str, Any]] = None
    pipeline_time_ms: float

class HeadlinesResponse(BaseModel):
    """Response for /api/v1/headlines."""
    success: bool = True
    fallback_tier: str
    data_vintage: str
    is_stale: bool = False
    staleness_warning: Optional[str] = None
    citation: Optional[str] = None
    total_headlines: int
    articles: List[Dict[str, Any]]
    sources_status: Dict[str, Any]

class DecisionActionRequest(BaseModel):
    """Request body for /api/v1/decision/action."""
    event_id: str = Field(..., description="Target event ID in the decision queue")
    action: str = Field(..., description="Action type: 'acknowledge', 'assign', 'comment', 'resolve'")
    officer: str = Field(default="Procurement Officer", description="Name or role of officer executing the action")
    notes: Optional[str] = Field(default="", description="Operational notes or comments")

class DecisionActionResponse(BaseModel):
    """Response for /api/v1/decision/action."""
    success: bool
    event_id: str
    status: str
    assigned_to: Optional[str] = None
    audit_trail: List[Dict[str, Any]]
    message: str

class HealthResponse(BaseModel):
    """Response for /health."""
    status: str
    mode: str
    data_vintage: str
    gpu_available: bool
    gpu_name: Optional[str] = None
    slm_available: bool
    slm_skip_reason: Optional[str] = None
    graph_nodes: int
    graph_edges: int
    graph_integrity: bool
    graph_hash: str
    baseline_crore: float
    usd_inr_rate: float
    version: str
    reasons: List[str] = Field(default_factory=list, description="Specific diagnostics for degraded or unhealthy status")


# ════════════════════════════════════════════════════════════════
# APP CONSTRUCTION
# ════════════════════════════════════════════════════════════════

# ── Startup Security Lifespan ──
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Validates that insecure default secrets/passwords are not used outside dev mode."""
    verify_security_configuration()
    yield

app = FastAPI(
    title="CounterVerse API",
    description=(
        "Causal AI supply chain disruption simulator for Indian automotive semiconductors. "
        "Headline → GraphRAG → Risk Score → Monte Carlo → Procurement Cost at Risk (PCaR). "
        "Enterprise-grade: OAuth2/JWT auth, Prometheus metrics, rate-limiting."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS Configuration (Restricted to Configured Origins) ──
_DEFAULT_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://localhost:8501",
    "http://127.0.0.1:8501",
]
_env_allowed_origins = os.getenv("COUNTERVERSE_ALLOWED_ORIGINS")
ALLOWED_ORIGINS: List[str] = (
    [o.strip() for o in _env_allowed_origins.split(",") if o.strip()]
    if _env_allowed_origins
    else _DEFAULT_ALLOWED_ORIGINS
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ── Request ID and Structured Logging Middleware ──
@app.middleware("http")
async def request_id_and_structured_logging(request: Request, call_next):
    req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    t0 = time.perf_counter()
    response: Response = await call_next(request)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    response.headers["X-Request-ID"] = req_id

    # Structured log
    log_record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": req_id,
        "method": request.method,
        "path": request.url.path,
        "status_code": response.status_code,
        "duration_ms": round(elapsed_ms, 2),
    }
    logger.info(json.dumps(log_record))
    return response

# ── Rate-limiter state ──
if _SLOWAPI_AVAILABLE and _limiter:
    app.state.limiter = _limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── Prometheus /metrics endpoint ──
if PROMETHEUS_AVAILABLE and _make_metrics_app:
    app.mount("/metrics", _make_metrics_app())

# ── Static files mount for generated reports ──
_STATIC_DIR = _PROJECT_ROOT / "static"
_STATIC_DIR.mkdir(parents=True, exist_ok=True)
(_STATIC_DIR / "reports").mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")


# ════════════════════════════════════════════════════════════════
# ENDPOINTS
# ════════════════════════════════════════════════════════════════

@app.post("/api/v1/analyze-headline", response_model=HeadlineResponse, dependencies=[Depends(require_authenticated)])
async def analyze_headline(req: HeadlineRequest):
    """
    Full pipeline: Headline → SLM Signal Extraction → GraphRAG Grounding →
    Deterministic Risk Score → Monte Carlo → PCaR Financial Quantification.
    """
    t0 = time.perf_counter()

    # 1. Signal extraction
    engine_used = req.engine
    if req.engine == "slm" and SLM_AVAILABLE:
        try:
            signal = extract_signal(
                req.headline,
                engine="slm",
                severity_pct_override=req.severity_pct_override,
                duration_days_override=req.duration_days_override,
            )
        except Exception as e:
            logger.warning(f"SLM inference failed: {e}. Falling back to fast.")
            signal = (
                extract_signal_fast(
                    req.headline,
                    severity_pct_override=req.severity_pct_override,
                    duration_days_override=req.duration_days_override,
                )
                if extract_signal_fast
                else _fallback_signal(
                    req.headline,
                    severity_pct_override=req.severity_pct_override,
                    duration_days_override=req.duration_days_override,
                )
            )
            engine_used = "fast (fallback)"
    elif extract_signal_fast:
        signal = extract_signal_fast(
            req.headline,
            severity_pct_override=req.severity_pct_override,
            duration_days_override=req.duration_days_override,
        )
        engine_used = "fast"
    else:
        signal = _fallback_signal(
            req.headline,
            severity_pct_override=req.severity_pct_override,
            duration_days_override=req.duration_days_override,
        )
        engine_used = "fallback"

    # 2. GraphRAG grounding
    grounding = ground_entities(signal)

    # 3. Deterministic risk scoring
    risk_result = calculate_deterministic_risk_score(signal)
    risk_score = risk_result.get("risk_score", 0.5)

    # Risk label
    risk_label = classify_risk_band(risk_score)

    # 4. Monte Carlo → PCaR
    probabilities = simulate_causal_impact(signal)
    mc_result = run_monte_carlo(probabilities, n_samples=req.mc_samples)

    # 5. PCaR calculation
    macro_pcar = calculate_pcar(mc_result, company_name="Entire Indian Automotive Industry")
    if req.company in ("Macro (aggregate)", "Entire Indian Automotive Industry"):
        pcar_metrics = _sanitize_pcar(macro_pcar)
    else:
        try:
            company_pcar = calculate_pcar_by_company(req.company, macro_pcar)
            pcar_metrics = _sanitize_pcar(company_pcar)
        except (ValueError, KeyError):
            pcar_metrics = _sanitize_pcar(calculate_pcar(mc_result, company_name=req.company))

    # 6. CSCO directive
    mean_crore = float(pcar_metrics.get("mean_loss_crore", pcar_metrics.get("pcar_mean_crore", 0.0)))
    directive_result = compute_cost_adjusted_recommendation(
        risk_score=risk_score,
        pcar_mean_crore=mean_crore
    )
    csco_directive = directive_result.get("recommendation", directive_result.get("cost_adjusted_best", "Monitor & Maintain"))

    elapsed_ms = (time.perf_counter() - t0) * 1000

    return HeadlineResponse(
        headline=req.headline,
        engine_used=engine_used,
        signal=_safe_dict(signal),
        grounding=grounding,
        risk_score=round(risk_score, 4),
        risk_label=risk_label,
        csco_directive=csco_directive,
        pcar_metrics=pcar_metrics,
        pipeline_time_ms=round(elapsed_ms, 1),
    )


class SignalExtractionRequest(BaseModel):
    headline: str = Field(..., min_length=5, max_length=500)
    engine: str = Field(default="fast")


@app.post("/api/v1/signal", tags=["Pipeline"], dependencies=[Depends(require_authenticated)])
async def extract_signal_endpoint(req: SignalExtractionRequest):
    """
    Extracts structured supply chain disruption signal from unstructured headline.
    """
    if req.engine == "slm" and SLM_AVAILABLE:
        try:
            signal = extract_signal(req.headline, engine="slm")
        except Exception:
            signal = extract_signal_fast(req.headline) if extract_signal_fast else _fallback_signal(req.headline)
    elif extract_signal_fast:
        signal = extract_signal_fast(req.headline)
    else:
        signal = _fallback_signal(req.headline)

    grounding = ground_entities(signal)
    return {
        "signal": _safe_dict(signal),
        "grounding": grounding,
        "engine_used": req.engine,
    }


@app.post("/api/v1/simulate", tags=["Pipeline"], dependencies=[Depends(require_authenticated)])
async def simulate_endpoint(signal_payload: Dict[str, Any]):
    """
    Propagates an extracted signal through causal scoring and Monte Carlo simulation.
    Accepts either an extracted signal directly or a dict wrapping { "signal": ... }.
    Accepts optional mc_samples (default: 10000) and seed/random_seed (default: 42).
    """
    sig = signal_payload.get("signal", signal_payload)
    risk_result = calculate_deterministic_risk_score(sig)
    risk_score = risk_result.get("risk_score", 0.5)
    risk_label = classify_risk_band(risk_score)

    mc_samples = int(signal_payload.get("mc_samples") or signal_payload.get("n_samples") or 10000)
    seed_val = signal_payload.get("seed")
    if seed_val is None:
        seed_val = signal_payload.get("random_seed")
    seed = int(seed_val) if seed_val is not None else 42

    probabilities = simulate_causal_impact(sig)
    mc_result = run_monte_carlo(probabilities, n_samples=mc_samples, random_seed=seed)

    pcar_macro = calculate_pcar(mc_result, company_name="Entire Indian Automotive Industry", random_seed=seed)
    directive_result = compute_cost_adjusted_recommendation(
        risk_score=risk_score,
        pcar_mean_crore=float(pcar_macro.get("mean_loss_crore", 0.0)),
    )

    return {
        "risk_score": round(risk_score, 4),
        "risk_label": risk_label,
        "risk_result": _safe_dict(risk_result),
        "factor_breakdown": risk_result.get("breakdown", {}),
        "probabilities": {k: v for k, v in probabilities.items() if not k.startswith("_") and not isinstance(v, dict)},
        "mc_stats": {
            "mean_drop": round(float(mc_result["mean_drop"]), 2),
            "p95_drop": round(float(mc_result["p95_drop"]), 2),
            "p99_drop": round(float(mc_result["p99_drop"]), 2),
            "n_samples": mc_result.get("n_samples", mc_samples),
        },
        "simulation_config": {
            "mc_samples": mc_samples,
            "random_seed": seed,
        },
        "pcar": _sanitize_pcar(pcar_macro),
        "csco_directive": directive_result.get("recommendation", "Maintain Standard Operations"),
        "metric_version": pcar_macro.get("metric_version", METRIC_VERSION),
        "assumptions": pcar_macro.get("assumptions"),
    }


@app.post("/api/v1/simulate-risk", response_model=SimulateResponse, dependencies=[Depends(require_analyst)])
async def simulate_risk(req: SimulateRequest):
    """
    Runs Monte Carlo simulation with custom parameters.
    Returns risk distribution statistics without requiring a headline.
    """
    t0 = time.perf_counter()

    # Build a synthetic signal from parameters
    synthetic_signal = {
        "event_type": req.event_type,
        "severity": req.severity,
        "duration_days": req.duration_days,
        "recovery_time_days": max(30, req.duration_days // 2),
        "affected_regions": ["China", "Taiwan"],
        "component": "Integrated Circuits",
        "impacted_industries": ["Automotive", "Semiconductors"],
        "companies": [],
    }

    risk_result = calculate_deterministic_risk_score(synthetic_signal)
    risk_score = risk_result.get("risk_score", 0.5)

    risk_label = classify_risk_band(risk_score)

    probabilities = simulate_causal_impact(synthetic_signal)
    mc_result = run_monte_carlo(
        probabilities,
        n_samples=req.mc_samples,
        random_seed=req.random_seed,
    )

    mc_stats = {
        "mean_drop_pct": mc_result["mean_drop"],
        "median_drop_pct": mc_result["median_drop"],
        "p95_drop_pct": mc_result["p95_drop"],
        "p99_drop_pct": mc_result["p99_drop"],
        "n_samples": mc_result["n_samples"],
    }

    # Remove numpy arrays for JSON serialization
    prob_safe = {k: v for k, v in probabilities.items() if k != "_risk_meta" and not isinstance(v, dict)}

    elapsed_ms = (time.perf_counter() - t0) * 1000

    return SimulateResponse(
        risk_score=round(risk_score, 4),
        risk_label=risk_label,
        probabilities=prob_safe,
        mc_stats=mc_stats,
        simulation_config={
            "event_type": req.event_type,
            "severity": req.severity,
            "duration_days": req.duration_days,
            "mc_samples": req.mc_samples,
            "random_seed": req.random_seed,
        },
        pipeline_time_ms=round(elapsed_ms, 1),
    )


@app.post("/api/v1/pcar/calculate", response_model=PcarResponse, tags=["Procurement Cost-at-Risk"], dependencies=[Depends(require_authenticated)])
@app.post("/api/v1/calculate-pcar", response_model=PcarResponse, dependencies=[Depends(require_authenticated)])
async def calculate_pcar_endpoint(req: PcarRequest):
    """
    Calculate Procurement Cost at Risk for a specific OEM or custom baseline.
    """
    t0 = time.perf_counter()

    # Build minimal signal for the requested risk score
    synthetic_signal = {
        "event_type": "supply_disruption",
        "severity": max(1, min(5, int(req.risk_score * 5) + 1)),
        "duration_days": 60,
        "recovery_time_days": 45,
        "affected_regions": ["China"],
        "component": "Integrated Circuits",
        "impacted_industries": ["Automotive"],
        "companies": [],
    }

    probabilities = simulate_causal_impact(synthetic_signal)
    mc_result = run_monte_carlo(probabilities, n_samples=req.mc_samples)

    baseline = req.custom_baseline_crore or SOURCED_HS8542_BASELINE_CRORE

    if req.company in ("Entire Indian Automotive Industry", "Macro (aggregate)"):
        pcar = calculate_pcar(
            mc_result,
            baseline_revenue_crore=baseline,
            company_name="Entire Indian Automotive Industry",
            baseline_output_value_crore=req.baseline_output_value_crore,
        )
    else:
        macro_pcar = calculate_pcar(
            mc_result,
            baseline_revenue_crore=baseline,
            company_name="Entire Indian Automotive Industry",
            baseline_output_value_crore=req.baseline_output_value_crore,
        )
        try:
            pcar = calculate_pcar_by_company(req.company, macro_pcar)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown company: '{req.company}'. Supported: {SUPPORTED_OEM_COMPANIES}"
            )

    elapsed_ms = (time.perf_counter() - t0) * 1000

    return PcarResponse(
        company_name=pcar.get("company_name", req.company),
        effective_base_crore=pcar.get("effective_base_crore", 0.0),
        mean_loss_crore=round(pcar.get("mean_loss_crore", 0.0), 2),
        pcar_95_crore=round(pcar.get("pcar_95_crore", 0.0), 2),
        pcar_99_crore=round(pcar.get("pcar_99_crore", 0.0), 2),
        worst_case_loss_crore=round(pcar.get("worst_case_loss_crore", 0.0), 2),
        extra_procurement_cost_mean_crore=round(pcar.get("extra_procurement_cost_mean_crore", 0.0), 2),
        extra_procurement_cost_p95_crore=round(pcar.get("extra_procurement_cost_p95_crore", 0.0), 2),
        extra_procurement_cost_p99_crore=round(pcar.get("extra_procurement_cost_p99_crore", 0.0), 2),
        lost_output_value_mean_crore=pcar.get("lost_output_value_mean_crore"),
        lost_output_value_p95_crore=pcar.get("lost_output_value_p95_crore"),
        lost_output_value_p99_crore=pcar.get("lost_output_value_p99_crore"),
        lost_output_value_status=pcar.get(
            "lost_output_value_status",
            "not_calculated_missing_output_value_baseline",
        ),
        market_share_pct=pcar.get("market_share_pct"),
        dependency_ratio_pct=pcar.get("dependency_ratio_pct"),
        data_provenance=pcar.get("data_provenance"),
        metric_version=pcar.get("metric_version", METRIC_VERSION),
        assumptions=pcar.get("assumptions"),
        pipeline_time_ms=round(elapsed_ms, 1),
    )


@app.post(
    "/api/v1/calculate-custom-bom",
    response_model=CustomBOMResponse,
    tags=["Procurement Cost-at-Risk"],
    summary="Compute enterprise PCaR from a custom Bill of Materials (BOM) with GraphRAG grounding",
    dependencies=[Depends(require_authenticated)],
)
async def calculate_custom_bom(req: CustomBOMRequest):
    """
    Computes enterprise-specific Procurement Cost-at-Risk (PCaR) from an OEM's
    custom Bill of Materials (component name, HS code, annual spend in ₹ Crore).
    
    Validates each line item against the supply-chain grounding graph and replaces
    the aggregate UN Comtrade macro baseline with the enterprise's actual BOM spend.
    """
    t0 = time.perf_counter()
    components_raw = [c.model_dump() for c in req.components]

    # Run Monte Carlo simulation based on input risk
    dummy_signal = {
        "event_type": "supply_disruption",
        "severity": min(5, max(1, int(req.risk_score * 5) + 1)),
        "duration_days": 30,
        "recovery_time_days": 30,
        "affected_regions": ["Taiwan", "East Asia"],
        "component": "Integrated Circuits",
        "impacted_industries": ["Automotive"],
        "companies": [req.company_name],
    }
    probs = simulate_causal_impact(dummy_signal)
    mc_result = run_monte_carlo(probs, n_samples=req.mc_samples)

    try:
        custom_pcar = calculate_pcar_custom_bom(
            mc_samples=mc_result,
            bom_components=components_raw,
            company_name=req.company_name,
            ground_against_graph=req.ground_against_graph,
            baseline_output_value_crore=req.baseline_output_value_crore,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    elapsed_ms = (time.perf_counter() - t0) * 1000

    return CustomBOMResponse(
        company_name=custom_pcar.get("company_name", req.company_name),
        effective_base_crore=float(custom_pcar.get("effective_base_crore", custom_pcar.get("total_baseline_crore", 0.0))),
        component_count=int(custom_pcar.get("component_count", custom_pcar.get("num_components", len(components_raw)))),
        mean_loss_crore=round(float(custom_pcar.get("mean_loss_crore", 0.0)), 2),
        pcar_95_crore=round(float(custom_pcar.get("pcar_95_crore", 0.0)), 2),
        pcar_99_crore=round(float(custom_pcar.get("pcar_99_crore", 0.0)), 2),
        worst_case_loss_crore=round(float(custom_pcar.get("worst_case_loss_crore", 0.0)), 2),
        extra_procurement_cost_mean_crore=round(float(custom_pcar.get("extra_procurement_cost_mean_crore", 0.0)), 2),
        extra_procurement_cost_p95_crore=round(float(custom_pcar.get("extra_procurement_cost_p95_crore", 0.0)), 2),
        extra_procurement_cost_p99_crore=round(float(custom_pcar.get("extra_procurement_cost_p99_crore", 0.0)), 2),
        lost_output_value_mean_crore=custom_pcar.get("lost_output_value_mean_crore"),
        lost_output_value_p95_crore=custom_pcar.get("lost_output_value_p95_crore"),
        lost_output_value_p99_crore=custom_pcar.get("lost_output_value_p99_crore"),
        lost_output_value_status=custom_pcar.get(
            "lost_output_value_status",
            "not_calculated_missing_output_value_baseline",
        ),
        component_grounding=custom_pcar.get("component_grounding", custom_pcar.get("grounding_results", [])),
        data_provenance=custom_pcar.get("data_provenance"),
        metric_version=custom_pcar.get("metric_version", METRIC_VERSION),
        assumptions=custom_pcar.get("assumptions"),
        pipeline_time_ms=round(elapsed_ms, 1),
    )


@app.get("/api/v1/health", response_model=HealthResponse)
async def health():
    """System health check: GPU, SLM, graph integrity, baselines."""
    G = get_grounding_graph()
    integrity = verify_graph_integrity(G)
    graph_hash = _compute_graph_hash(G)

    reasons: List[str] = []
    GOLDEN_HASH = "31f67108669b9208"

    # 1. Critical graph health checks
    if not integrity:
        reasons.append("Graph integrity verification failed (topology disconnected or invalid)")
    if graph_hash != GOLDEN_HASH:
        reasons.append(f"Graph hash mismatch: expected {GOLDEN_HASH}, computed {graph_hash}")

    # 2. SLM and GPU availability
    if not SLM_AVAILABLE:
        reasons.append(f"SLM inference unavailable: {_SLM_SKIP_REASON or 'Not loaded'} (fast heuristic active)")

    # 3. Custom overlay presence
    overlay_path = _PROJECT_ROOT / "data" / "processed" / "grounding_graph_custom.json"
    if not overlay_path.exists():
        reasons.append("Grounding graph custom overlay file missing from disk")

    # 4. Headline cache database staleness check
    cache_db_path = _PROJECT_ROOT / "data" / "processed" / "headline_cache.db"
    if not cache_db_path.exists():
        reasons.append("Headline cache database missing from disk")
    else:
        try:
            mtime = cache_db_path.stat().st_mtime
            age_hours = (time.time() - mtime) / 3600.0
            if age_hours > 24.0:
                reasons.append(f"Headline cache is stale ({age_hours:.1f} hours old, threshold 24h)")
        except Exception:
            pass

    # Status classification: unhealthy if graph broken or hash mismatch; degraded if warnings exist; otherwise healthy
    if not integrity or graph_hash != GOLDEN_HASH:
        status_code = "unhealthy"
    elif reasons:
        status_code = "degraded"
    else:
        status_code = "healthy"

    gpu_name = None
    if _HAS_GPU:
        try:
            import torch
            gpu_name = torch.cuda.get_device_name(0)
        except Exception:
            pass

    comtrade_data = load_comtrade_data()

    return HealthResponse(
        status=status_code,
        mode="slm" if SLM_AVAILABLE else "fast",
        data_vintage=str(comtrade_data.get("data_vintage", "2022 Full Year")),
        gpu_available=_HAS_GPU,
        gpu_name=gpu_name,
        slm_available=SLM_AVAILABLE,
        slm_skip_reason=_SLM_SKIP_REASON,
        graph_nodes=G.number_of_nodes(),
        graph_edges=G.number_of_edges(),
        graph_integrity=integrity,
        graph_hash=graph_hash,
        baseline_crore=float(SOURCED_HS8542_BASELINE_CRORE),
        usd_inr_rate=USD_INR_RATE,
        version="2.0.0",
        reasons=reasons,
    )


@app.get(
    "/api/v1/headlines",
    response_model=HeadlinesResponse,
    tags=["Ingestion"],
    summary="Fetch live or cached supply chain disruption headlines with resilient 4-tier fallback",
    dependencies=[Depends(require_authenticated)],
)
async def get_headlines_endpoint(max_records: int = 8):
    """
    Retrieves supply chain disruption headlines using a 4-tier fallback chain:
      1. GDELT 2.0 API (live)
      2. Google News RSS (live fallback)
      3. SQLite cached headlines (recent)
      4. Static fallback cache (last resort)

    Surfaces data provenance, vintage, staleness warnings, and source statuses (including Twitter).
    """
    res = fetch_headlines_resilient(max_records=max_records)
    tw_status = _fetch_twitter()

    tier = res.get("fallback_tier", "UNKNOWN")
    sources_status = {
        "gdelt": "active" if tier == "GDELT_LIVE" else "fallback_triggered",
        "rss": "active" if tier in ("GDELT_LIVE", "RSS_LIVE") else "fallback_triggered",
        "sqlite": "available",
        "twitter": {
            "status": tw_status.get("status", "not_configured"),
            "message": tw_status.get("message", "Twitter credentials not configured (COUNTERVERSE_TWITTER_BEARER_TOKEN missing)"),
        },
    }

    articles = res.get("articles", [])

    return HeadlinesResponse(
        success=bool(res.get("success", True)),
        fallback_tier=tier,
        data_vintage=res.get("data_vintage", "UNKNOWN"),
        is_stale=bool(res.get("is_stale", False)),
        staleness_warning=res.get("staleness_warning"),
        citation=res.get("citation"),
        total_headlines=len(articles),
        articles=articles,
        sources_status=sources_status,
    )

# ════════════════════════════════════════════════════════════════
# DECISION SUPPORT REPORT ENDPOINT
# ════════════════════════════════════════════════════════════════

class ReportRequest(BaseModel):
    """Request body for /generate-report."""
    headline: str = Field(..., min_length=5, max_length=500, description="News headline text")
    oem: str = Field(default="Maruti Suzuki", description="Target OEM")
    engine: str = Field(default="fast", description="Inference engine: 'fast' or 'slm'")
    mc_samples: Optional[int] = Field(default=10000, ge=100, le=500000, description="Monte Carlo sample count")

    model_config = {"extra": "ignore"}

class ReportResponse(BaseModel):
    """Response for /generate-report containing decision support report."""
    explanation: str
    estimated_impact: str
    recommended_action: str
    risk_score: float
    risk_breakdown: Dict[str, Any]
    mc_stats: Dict[str, Any]
    pcar: Dict[str, Any]  # Kept for backward compatibility (carries recommendation)
    pcar_metrics: Optional[Dict[str, Any]] = None  # Financial PCaR exposure metrics
    recommendation: Optional[Dict[str, Any]] = None  # Cost-adjusted decision directive
    metric_version: Optional[str] = "2.0.0"
    assumptions: Optional[Dict[str, Any]] = None
    report_url: str

@app.post("/api/v1/generate-report", response_model=ReportResponse, dependencies=[Depends(require_authenticated)])
async def generate_report_endpoint(req: ReportRequest):
    """Generate executive decision support report running the full server-side pipeline."""
    # 1. Sanitize headline
    clean_headline, _ = sanitize_headline(req.headline)

    # 2. Extract signal
    engine_used = req.engine
    if req.engine == "slm" and SLM_AVAILABLE:
        try:
            signal = extract_signal(
                clean_headline,
                engine="slm",
            )
        except Exception as e:
            logger.warning(f"SLM inference failed: {e}. Falling back to fast.")
            signal = (
                extract_signal_fast(clean_headline)
                if extract_signal_fast
                else _fallback_signal(clean_headline)
            )
            engine_used = "fast (fallback)"
    elif extract_signal_fast:
        signal = extract_signal_fast(clean_headline)
        engine_used = "fast"
    else:
        signal = _fallback_signal(clean_headline)
        engine_used = "fallback"

    # 3. GraphRAG grounding
    grounding = ground_entities(signal)

    # 4. Deterministic risk scoring
    risk_result = calculate_deterministic_risk_score(signal)
    risk_score = risk_result.get("risk_score", 0.5)

    risk_label = classify_risk_band(risk_score)

    # 5. Monte Carlo simulation
    probabilities = simulate_causal_impact(signal)
    samples = req.mc_samples if req.mc_samples else 10000
    mc_result = run_monte_carlo(probabilities, n_samples=samples)

    # 6. PCaR calculation for selected OEM
    macro_pcar = calculate_pcar(mc_result, company_name="Entire Indian Automotive Industry")
    company = req.oem if req.oem else "Maruti Suzuki"
    if company in ("Macro (aggregate)", "Entire Indian Automotive Industry"):
        pcar_metrics = _sanitize_pcar(macro_pcar)
    else:
        try:
            company_pcar = calculate_pcar_by_company(company, macro_pcar)
            pcar_metrics = _sanitize_pcar(company_pcar)
        except (ValueError, KeyError):
            pcar_metrics = _sanitize_pcar(calculate_pcar(mc_result, company_name=company))

    pipeline_result = {
        "headline": clean_headline,
        "engine_used": engine_used,
        "target_oem": company,
        "signal": signal,
        "grounding": grounding,
        "risk_result": risk_result,
        "risk_score": risk_score,
        "risk_label": risk_label,
        "mc_result": mc_result,
        "pcar_metrics": pcar_metrics,
    }

    report = generate_report(pipeline_result)
    return ReportResponse(**report)



# ── Auth token endpoint ──────────────────────────────────────────
from fastapi.security import OAuth2PasswordRequestForm

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

@app.post("/api/v1/token", response_model=TokenResponse, tags=["Auth"])
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Obtain a JWT Bearer token with user roles.
    Default credentials (dev mode):
      - admin / changeme (roles: admin, officer, analyst)
      - officer / officerpass (roles: officer)
      - analyst / analystpass (roles: analyst)
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    token = create_access_token(data={"sub": user["username"], "roles": user.get("roles", [])})
    return TokenResponse(access_token=token, token_type="bearer")


# ── Currency conversion helper ───────────────────────────────────
CURRENCY_RATES = {
    "INR": 1.0,
    "USD": 1.0 / USD_INR_RATE,
    "EUR": 1.0 / (USD_INR_RATE * 1.08),  # approximate EUR/INR via USD/EUR 1.08
}

@app.get("/api/v1/currencies", tags=["Utilities"], dependencies=[Depends(require_authenticated)])
async def get_supported_currencies():
    """Returns supported output currencies for PCaR and their INR conversion rates."""
    return {"supported": list(CURRENCY_RATES.keys()), "base": "INR"}


@app.get("/api/v1/backtest/siam", tags=["Model Validation"], dependencies=[Depends(require_analyst)])
async def get_siam_backtest():
    """
    Returns dynamically computed SIAM 2021 historical benchmark backtest results.
    Loads from precomputed data/siam_backtest_results.json or computes on the fly if missing.
    """
    results_path = _PROJECT_ROOT / "data" / "siam_backtest_results.json"
    if results_path.exists():
        try:
            with open(results_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to read {results_path}: {e}")

    try:
        from scripts.run_siam_backtest import run_siam_backtest
        return run_siam_backtest(seed=42, n_samples=10000)
    except Exception as e:
        logger.error(f"Failed to compute SIAM backtest on the fly: {e}")
        raise HTTPException(status_code=500, detail=f"SIAM backtest computation failed: {str(e)}")


# ── Live Web Scraping Endpoints ──────────────────────────────────
@app.get("/api/v1/live-news", tags=["News Ingestion"], dependencies=[Depends(require_authenticated)])
@app.get("/api/v1/scrape-news", tags=["News Ingestion"], dependencies=[Depends(require_authenticated)])
async def get_live_news_endpoint(max_total: int = 6):
    """
    Live web scraping endpoint:
    Scrapes real-time supply chain disruption news from Google News RSS & GDELT 2.0,
    evaluates disruption scores, and returns structured headlines for UI ingestion.
    """
    try:
        from src.news_scraper import scrape_live_supply_chain_news
        res = scrape_live_supply_chain_news(max_total=max_total)
        return res
    except Exception as e:
        logger.error(f"Live news scrape failed: {e}")
        raise HTTPException(status_code=500, detail=f"Live news scrape failed: {str(e)}")



# ════════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════════

def _fallback_signal(
    headline: str,
    severity_pct_override: Optional[int] = None,
    duration_days_override: Optional[int] = None,
) -> dict:
    """Minimal signal when no SLM or heuristic is available."""
    return {
        "event_type": "supply_disruption",
        "severity": 3,
        "severity_pct": severity_pct_override if severity_pct_override is not None else 75,
        "duration_days": duration_days_override if duration_days_override is not None else 30,
        "recovery_time_days": 30,
        "affected_regions": [],
        "component": "Integrated Circuits",
        "impacted_industries": ["Automotive", "Semiconductors"],
        "companies": [],
        "headline": headline,
        "engine": "api_fallback",
    }


def _sanitize_pcar(pcar: dict) -> dict:
    """Remove internal sample arrays from PCaR results for JSON serialization."""
    return {k: v for k, v in pcar.items() if not k.startswith("_")}


def _safe_dict(d: Any) -> dict:
    """Ensure dict output even for non-dict returns."""
    if isinstance(d, dict):
        return {k: v for k, v in d.items() if not hasattr(v, '__array__') or isinstance(v, (int, float, str, bool, list))}
    return {"raw": str(d)}


# ════════════════════════════════════════════════════════════════
# DECISION MODE QUEUE AND ACTIONS STORE (Phase 6)
# ════════════════════════════════════════════════════════════════

_DECISION_QUEUE_FILE = _PROJECT_ROOT / "data" / "decision_queue.json"

def _load_decision_queue() -> List[Dict[str, Any]]:
    if not _DECISION_QUEUE_FILE.exists():
        return []
    try:
        with open(_DECISION_QUEUE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading decision queue: {e}")
        return []

def _save_decision_queue(queue: List[Dict[str, Any]]) -> None:
    _DECISION_QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(_DECISION_QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(queue, f, indent=2, ensure_ascii=False)


@app.get("/api/v1/decision/events", tags=["Decision Mode"], dependencies=[Depends(require_authenticated)])
async def get_decision_events():
    """
    Returns the ranked decision event queue for procurement and supply-chain officers.
    Includes human-in-the-loop authorization policy, risk bands, exposure ranges, and audit trails.
    """
    queue = _load_decision_queue()
    return {
        "success": True,
        "policy": "Never auto-execute purchases or supplier changes; recommendations require human officer approval.",
        "total_events": len(queue),
        "events": queue,
    }


@app.post("/api/v1/decision/action", response_model=DecisionActionResponse, tags=["Decision Mode"], dependencies=[Depends(require_officer)])
async def record_decision_action(req: DecisionActionRequest):
    """
    Executes a procurement officer workflow action on a queued disruption event:
    - acknowledge: Officer confirms receipt and triage of threat
    - assign: Delegates event to a specialist desk or officer
    - comment: Adds operational annotations or supplier communications
    - resolve: Final sign-off and approval of mitigation plan
    All actions are timestamped and appended to the persistent audit log.
    """
    queue = _load_decision_queue()
    target_event = None
    for evt in queue:
        if evt.get("id") == req.event_id:
            target_event = evt
            break

    if not target_event:
        raise HTTPException(status_code=404, detail=f"Event '{req.event_id}' not found in decision queue.")

    now_utc = datetime.now(timezone.utc).isoformat()
    action_type = req.action.lower().strip()

    if "audit_trail" not in target_event:
        target_event["audit_trail"] = []

    if action_type == "acknowledge":
        target_event["status"] = "ACKNOWLEDGED"
        msg = f"Event {req.event_id} acknowledged by {req.officer}."
    elif action_type == "assign":
        target_event["assigned_to"] = req.officer
        target_event["status"] = "IN_REVIEW"
        msg = f"Event {req.event_id} assigned to {req.officer}."
    elif action_type == "comment":
        msg = f"Comment added to {req.event_id} by {req.officer}."
    elif action_type == "resolve":
        target_event["status"] = "RESOLVED"
        msg = f"Event {req.event_id} approved and resolved by {req.officer}."
    else:
        raise HTTPException(status_code=400, detail=f"Invalid action '{req.action}'. Supported: acknowledge, assign, comment, resolve.")

    target_event["audit_trail"].append({
        "action": action_type,
        "actor": req.officer,
        "timestamp": now_utc,
        "notes": req.notes or msg,
    })

    _save_decision_queue(queue)

    return DecisionActionResponse(
        success=True,
        event_id=req.event_id,
        status=target_event["status"],
        assigned_to=target_event.get("assigned_to"),
        audit_trail=target_event["audit_trail"],
        message=msg,
    )

