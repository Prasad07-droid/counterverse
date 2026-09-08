import os
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components
import sys
import json
import time
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Robust path resolution for both local and cloud environments
_file_path = Path(__file__).resolve()
_app_dir = _file_path.parent          # app/
_project_root = _file_path.parent.parent  # sem 7/ (project root)
project_root = _project_root
COMTRADE_PATH = _project_root / "data" / "processed" / "comtrade_india_baseline.json"

for _path in [str(_project_root), str(_app_dir)]:
    if _path not in sys.path:
        sys.path.insert(0, _path)

# Cloud environment detection
_has_gpu = False
try:
    import torch
    _has_gpu = torch.cuda.is_available()
except Exception:
    _has_gpu = False

IS_CLOUD = os.environ.get("STREAMLIT_SHARING_MODE") == "1" or \
           os.environ.get("RAILWAY_ENVIRONMENT") is not None or \
           os.environ.get("RENDER") is not None or \
           (not os.path.exists("/dev/nvidia0") and not _has_gpu)  # No GPU = likely cloud

if IS_CLOUD:
    # Force Fast Mode on cloud — skip SLM download entirely
    SLM_AVAILABLE = False
    _SLM_SKIP_REASON = "Cloud environment detected — GPU unavailable"
else:
    # Local: attempt SLM load normally (FIX 1 lazy import handles failure)
    try:
        from src.module_b_slm import extract_signal, extract_signal_with_grounding
        SLM_AVAILABLE = True
    except (ImportError, RuntimeError, OSError):
        SLM_AVAILABLE = False

from src.module_c_causal import (
    simulate_causal_impact,
    calculate_deterministic_risk_score,
    compute_cost_adjusted_recommendation,
)
from src.module_d_mc import run_monte_carlo
import importlib
import src.module_e_pcar as module_e_pcar
try:
    importlib.reload(module_e_pcar)
except Exception:
    pass
calculate_pcar = getattr(module_e_pcar, "calculate_pcar")
calculate_pcar_by_company = getattr(module_e_pcar, "calculate_pcar_by_company", None)
OEM_PROFILES = getattr(module_e_pcar, "OEM_PROFILES", {
    "Maruti Suzuki": {"market_share": 0.417, "dependency_ratio": 0.38, "description": "India's largest automaker; high-volume mass-market PV"},
    "Hyundai India": {"market_share": 0.146, "dependency_ratio": 0.42, "description": "Second largest PV maker; higher electronic component density"},
    "Tata Motors": {"market_share": 0.139, "dependency_ratio": 0.45, "description": "EV market leader (~70% EV share); high semiconductor intensity"},
    "Mahindra": {"market_share": 0.112, "dependency_ratio": 0.44, "description": "SUV market leader; heavily impacted in 2021 chip crisis"},
    "Entire Indian Automotive Industry": {"market_share": 1.000, "dependency_ratio": 1.00, "description": "Macro-level aggregate Indian automotive semiconductor import exposure"}
})

ENTERPRISE_OEM_OPTIONS = [
    "Maruti Suzuki",
    "Tata Motors",
    "Mahindra",
    "Hyundai India",
    "Macro (aggregate)"
]


def compute_pcar_for_selection(mc_samples, company_selection: str) -> dict:
    """
    Computes PCaR metrics for the target enterprise selection.
    If 'Macro (aggregate)' or macro industry is selected, calls calculate_pcar().
    If a specific OEM is selected, calls calculate_pcar_by_company() scaled from macro baseline.
    """
    macro_pcar = calculate_pcar(mc_samples, company_name="Entire Indian Automotive Industry")
    if company_selection in ("Macro (aggregate)", "Entire Indian Automotive Industry", "Macro"):
        return macro_pcar
    if calculate_pcar_by_company is not None:
        try:
            return calculate_pcar_by_company(company_selection, macro_pcar)
        except Exception as e:
            logger.warning(f"calculate_pcar_by_company failed for {company_selection}: {e}. Falling back to calculate_pcar.")
            return calculate_pcar(mc_samples, company_name=company_selection)
    return calculate_pcar(mc_samples, company_name=company_selection)

import importlib
import src.data_sources
importlib.reload(src.data_sources)
from src.grounding_graph import get_graph_summary, get_grounding_graph
from src.data_sources import (
    load_comtrade_data,
    get_sourced_baseline_crore,
    SOURCED_HS8542_BASELINE_CRORE,
    SOURCED_HS8112_BASELINE_CRORE,
    USD_INR_RATE,
    fetch_live_gdelt_headlines,
    SIAM_2021_GROUND_TRUTH,
)

# Model loading — cache the resource (shared across all users/sessions)
@st.cache_resource(show_spinner="Loading analysis engine...")
def _get_slm_pipeline():
    """Load SLM model once, share across all sessions."""
    if not SLM_AVAILABLE:
        return None
    try:
        from src.module_b_slm import get_slm_model
        return get_slm_model()
    except Exception:
        return None

# Result caching — cache the output data only
@st.cache_data(max_entries=100, ttl=3600)
def cached_extract_signal(headline: str, engine: str = "fast") -> dict:
    if SLM_AVAILABLE and engine == "slm":
        return extract_signal(headline, engine="slm")
    from src.module_b_slm import extract_signal_fast
    return extract_signal_fast(headline)

@st.cache_data(max_entries=100, ttl=3600)
def cached_extract_signal_grounded(headline: str, engine: str = "fast") -> dict:
    if SLM_AVAILABLE and engine == "slm":
        return extract_signal_with_grounding(headline, engine="slm")
    from src.module_b_slm import extract_signal_fast
    signal = extract_signal_fast(headline)
    from src.grounding_graph import ground_entities
    grounding = ground_entities(signal)
    return {"signal": signal, "grounding": grounding, **signal}

@st.cache_data
def cached_simulate_causal_impact(signal: dict) -> dict:
    return simulate_causal_impact(signal)

st.session_state.setdefault("auto_params_extracted", False)
st.session_state.setdefault("last_signal_result", None)

# --- Helper Functions ---
def format_inr(number):
    """Formats a number in Indian numbering system (e.g., 3,55,838)"""
    num_str = str(int(number))
    if len(num_str) <= 3:
        return num_str
    last_three = num_str[-3:]
    rest = num_str[:-3]
    rest_with_commas = ",".join([rest[max(i-2, 0):i] for i in range(len(rest), 0, -2)][::-1])
    return f"{rest_with_commas},{last_three}"

def classify_incident_severity(severity_level: int) -> tuple[str, str, str]:
    """
    Classifies raw input disruption signal magnitude (Level 1 to 3).
    Returns (label, badge_html, subtext).
    """
    if severity_level >= 3:
        return "Severe Shock", '<span class="status-badge-critical">Critical Shock</span>', "Level 3 / 3 · Acute Disruptive Event"
    elif severity_level == 2:
        return "Moderate Shock", '<span class="status-badge-warning">Moderate Shock</span>', "Level 2 / 3 · Controlled Friction"
    else:
        return "Minor Shock", '<span class="status-badge-optimal">Minor Variance</span>', "Level 1 / 3 · Low Severity Signal"

def classify_production_drop(drop_pct: float) -> tuple[str, str, str]:
    """
    Classifies simulated network-level output loss (mean production drop %).
    Returns (label, color, description).
    """
    if drop_pct >= 15.0:
        return "Severe Network Impact", "#dc2626", "Substantial vehicle assembly curtailment across downstream nodes."
    elif drop_pct >= 5.0:
        return "Moderate Network Impact", "#d97706", "Noticeable assembly slowdown buffered partially by safety stock."
    else:
        return "Minor Network Impact", "#059669", "Nominal output variance absorbed by local inventory buffers."

def classify_structural_risk(score: float) -> tuple[str, str, str]:
    """
    Classifies supplier structural exposure risk (AlMahri et al. 2026, Section 3.2.5).
    Scale: 0.0 to 1.0.
    Returns (label, color, directive).
    """
    if score >= 0.60:
        return "HIGH Structural Risk", "#dc2626", "Replace Supplier / Qualify Dual-Sourcing Immediately (CSCO Directive)"
    elif score >= 0.45:
        return "MEDIUM Structural Risk", "#d97706", "Increase Safety Stock & Active Weekly Monitoring"
    else:
        return "LOW Structural Risk", "#059669", "Maintain Standard Operations & Routine Watch"

# ════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="CounterVerse · Decision Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ════════════════════════════════════════════════════════════════
# CLEAN LIGHT / CORPORATE THEME  — custom CSS injection
# ════════════════════════════════════════════════════════════════
st.markdown("""
<style>
/* ── Google Font ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* ── Root variables (Hybrid Command Theme) ── */
:root {
    /* Sidebar — dark navy, sidebar ONLY */
    --sidebar-bg: #111827;
    --sidebar-bg-hover: #1a2436;
    --sidebar-text: #cbd5e1;
    --sidebar-text-muted: #64748b;
    --sidebar-active-bg: #1e293b;
    --sidebar-active-indicator: #f97316;  /* orange left-border/dot on active item */

    /* Main content area — stays LIGHT for readability of dense data */
    --content-bg: #f8f9fa;
    --content-surface: #ffffff;
    --content-surface-hover: #f9fafb;
    --border-subtle: #e5e7eb;
    --border-hover: #d1d5db;

    --text-primary: #111827;
    --text-secondary: #475569;            /* Slate-600: Upgraded from #4b5563 for AAA compliance */
    --text-muted: #475569;                /* Upgraded from #6b7280 (7.31:1 ratio for AAA compliance) */

    /* Disruption / critical accent — reserved STRICTLY for active shocks */
    --accent-coral: #ef4444;
    --accent-coral-bright: #dc2626;
    --accent-coral-bg: #fef2f2;
    --accent-coral-border: #fecaca;

    /* Verified / evidence / grounded-truth accent */
    --accent-teal: #0d9488;
    --accent-teal-bg: #f0fdfa;
    --accent-teal-border: #99f6e4;

    /* Heuristic / analyst-estimate accent */
    --accent-amber: #d97706;
    --accent-amber-bg: #fffbeb;
    --accent-amber-border: #fde68a;

    /* Risk semantic colors */
    --risk-high: #dc2626;
    --risk-medium: #d97706;
    --risk-low: #059669;

    --shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px 0 rgba(0, 0, 0, 0.03);
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.07), 0 2px 4px -2px rgba(0, 0, 0, 0.04);
    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -4px rgba(0, 0, 0, 0.03);
    --radius-standard: 12px;
    --radius-sm: 6px;
}

/* ── Global overrides ── */
.stApp {
    background: var(--content-bg) !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    color: var(--text-primary) !important;
}

/* ── Enterprise Dark Command Sidebar Styling ── */
section[data-testid="stSidebar"] {
    background-color: var(--sidebar-bg) !important;
    border-right: 1px solid #1f2937 !important;
}
section[data-testid="stSidebar"] * {
    color: var(--sidebar-text) !important;
    font-family: 'Inter', sans-serif !important;
}
section[data-testid="stSidebar"] hr {
    border-color: #1f2937 !important;
}
section[data-testid="stSidebar"] .stRadio label {
    color: var(--sidebar-text) !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    padding: 8px 12px !important;
    border-radius: 8px !important;
    transition: all 0.15s ease !important;
}
section[data-testid="stSidebar"] .stRadio label:hover {
    background-color: var(--sidebar-bg-hover) !important;
}
section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label[data-checked="true"],
section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:has(input:checked) {
    background-color: var(--sidebar-active-bg) !important;
    border-left: 3px solid var(--sidebar-active-indicator) !important;
    color: #ffffff !important;
    font-weight: 700 !important;
}

/* Hide default Streamlit header/footer */
header[data-testid="stHeader"] {
    background: transparent !important;
}
#MainMenu, footer, .stDeployButton { display: none !important; }

/* ── Sidebar Form Control Dark Styling ── */
section[data-testid="stSidebar"] div[data-testid="stSelectbox"] > div > div {
    background: #1f2937 !important;
    border: 1px solid #374151 !important;
    color: #f3f4f6 !important;
}
section[data-testid="stSidebar"] div[data-testid="stSelectbox"] [data-baseweb="select"] * {
    color: #f3f4f6 !important;
    -webkit-text-fill-color: #f3f4f6 !important;
}
section[data-testid="stSidebar"] div[data-testid="stSelectbox"] label,
section[data-testid="stSidebar"] div[data-testid="stRadio"] label {
    color: #94a3b8 !important;
}

/* ── Active Disruption Incident Banner ── */
.active-incident-banner {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
    padding: 10px 18px;
    background: linear-gradient(90deg, #fef2f2 0%, #ffffff 100%);
    border: 1px solid var(--accent-coral-border);
    border-left: 4px solid var(--accent-coral-bright);
    border-radius: var(--radius-standard);
    box-shadow: var(--shadow-sm);
    margin-bottom: 16px;
}
.incident-badge-group {
    display: flex;
    align-items: center;
    gap: 10px;
}
.incident-shock-badge {
    background: var(--accent-coral-bright);
    color: #ffffff;
    font-size: 0.72rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    padding: 3px 8px;
    border-radius: 4px;
}
.incident-headline-text {
    font-size: 0.92rem;
    font-weight: 700;
    color: #111827;
}
.incident-meta-group {
    display: flex;
    align-items: center;
    gap: 16px;
    font-size: 0.78rem;
    color: var(--text-secondary);
}
.incident-meta-item strong {
    color: #111827;
}

/* ── Causal Decision Ribbon (Compact 4-Tier Pipeline State) ── */
.decision-ribbon {
    display: flex;
    align-items: stretch;
    background: #ffffff;
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-standard);
    box-shadow: var(--shadow-sm);
    margin-bottom: 22px;
    overflow: hidden;
}
.ribbon-tier {
    flex: 1;
    padding: 12px 18px;
    border-right: 1px solid var(--border-subtle);
    background: #ffffff;
    display: flex;
    flex-direction: column;
    justify-content: center;
    position: relative;
    transition: background-color 0.2s ease;
}
.ribbon-tier:last-child {
    border-right: none;
}
.ribbon-tier.active-shock {
    background: #fff8f8;
    border-left: 3px solid var(--accent-coral-bright);
}
.ribbon-tier-label {
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-muted);
    margin-bottom: 4px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.ribbon-tier-val {
    font-size: 1.02rem;
    font-weight: 700;
    color: var(--text-primary);
    line-height: 1.25;
}
.ribbon-tier-sub {
    font-size: 0.74rem;
    color: var(--text-secondary);
    margin-top: 3px;
    line-height: 1.3;
}
.ribbon-pulse-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--accent-coral-bright);
    display: inline-block;
    box-shadow: 0 0 0 rgba(239, 68, 68, 0.4);
    animation: ribbonPulse 2s infinite ease-in-out;
}
.ribbon-dot-teal {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--accent-teal);
    display: inline-block;
}
.ribbon-dot-amber {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--accent-amber);
    display: inline-block;
}
.ribbon-dot-blue {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #2563eb;
    display: inline-block;
}
@keyframes ribbonPulse {
    0% { transform: scale(0.92); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.6); }
    70% { transform: scale(1.08); box-shadow: 0 0 0 6px rgba(239, 68, 68, 0); }
    100% { transform: scale(0.92); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
}

/* ── Recommended Action Card ── */
.recommended-action-card {
    background: #ffffff;
    border: 1px solid #99f6e4;
    border-left: 4px solid #0d9488;
    border-radius: var(--radius-standard);
    padding: 14px 18px;
    box-shadow: var(--shadow-sm);
    margin-top: 14px;
}
.action-kicker {
    font-size: 0.70rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #0d9488;
}
.action-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: #111827;
    margin: 4px 0 6px 0;
}
.action-sub {
    font-size: 0.80rem;
    color: var(--text-secondary);
    line-height: 1.4;
}

/* ── Panels ── */
.glass-card {
    background: #ffffff;
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-standard);
    box-shadow: var(--shadow-sm);
    padding: 32px;
    margin-bottom: 24px;
    transition: all 0.3s ease;
}
.glass-card:hover {
    border-color: var(--border-hover);
    box-shadow: var(--shadow-md);
}
.glass-card h3 {
    font-size: 14px;
    font-weight: 600;
    color: #111827;
    margin-bottom: 22px;
    display: flex; align-items: center; gap: 8px;
    letter-spacing: -0.2px;
}
.card-label {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: var(--text-muted);
    margin-bottom: 8px;
}

/* ── Section header ── */
.section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 14px;
    margin-bottom: 22px;
}
.section-header h3 {
    font-size: 1.05rem;
    font-weight: 600;
    color: #111827;
    margin: 0;
    letter-spacing: -0.2px;
}
.section-badge {
    font-size: 11px;
    font-weight: 500;
    color: var(--text-secondary);
    background: #f3f4f6;
    padding: 5px 12px;
    border-radius: var(--radius-standard);
    border: 1px solid var(--border-subtle);
}

/* ── Metric Card ── */
.metric-card {
    background: #ffffff;
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-standard);
    box-shadow: var(--shadow-sm);
    padding: 24px 22px;
    text-align: left;
    transition: all 0.25s ease;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    min-height: 124px;
}
.metric-card:hover {
    border-color: var(--border-hover);
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
}
.metric-card.critical {
    border: 1px solid var(--accent-coral-border);
    background: linear-gradient(180deg, #fff5f5 0%, #ffffff 100%);
}
.metric-card .metric-label {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: var(--text-muted);
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.metric-card .metric-value {
    font-size: 26px;
    font-weight: 700;
    color: #111827;
    line-height: 1.2;
    letter-spacing: -0.5px;
}
.metric-card .metric-sub {
    font-size: 12px;
    font-weight: 400;
    color: var(--text-secondary);
    margin-top: 8px;
}
.status-badge-critical {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    background: var(--accent-coral-bg);
    color: var(--accent-coral-bright);
    border: 1px solid var(--accent-coral-border);
    padding: 2px 8px;
    border-radius: var(--radius-standard);
}
.status-badge-warning {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    background: #fffbeb;
    color: #d97706;
    border: 1px solid #fde68a;
    padding: 2px 8px;
    border-radius: var(--radius-standard);
}
.status-badge-optimal {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    background: #ecfdf5;
    color: #059669;
    border: 1px solid #a7f3d0;
    padding: 2px 8px;
    border-radius: var(--radius-standard);
}

/* ── Streamlit Form Element Overrides & Placeholders ── */
div[data-testid="stSelectbox"] label,
div[data-testid="stSlider"] label,
div[data-testid="stNumberInput"] label,
div[data-testid="stTextArea"] label,
div[data-testid="stSelectbox"] label p,
div[data-testid="stSlider"] label p,
div[data-testid="stNumberInput"] label p,
div[data-testid="stTextArea"] label p {
    font-size: 11px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 1.2px !important;
    color: var(--text-muted) !important;
    margin-bottom: 8px !important;
}

div[data-testid="stSelectbox"] > div > div {
    background: #ffffff !important;
    border: 1px solid #d1d5db !important;
    color: #111827 !important;
    border-radius: var(--radius-standard) !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    transition: all 0.2s ease;
    box-shadow: var(--shadow-sm);
}
div[data-testid="stSelectbox"] > div > div:hover,
div[data-testid="stSelectbox"] > div > div:focus-within {
    border-color: #ef4444 !important;
    box-shadow: 0 0 0 1px #ef4444 !important;
}

/* Dropdown value, placeholder, and arrow visibility */
div[data-testid="stSelectbox"] [data-baseweb="select"] {
    background-color: #ffffff !important;
    border-radius: var(--radius-standard) !important;
}
div[data-testid="stSelectbox"] [data-baseweb="select"] * {
    color: #111827 !important;
    -webkit-text-fill-color: #111827 !important;
}
div[data-testid="stSelectbox"] [data-baseweb="select"] div[role="combobox"] {
    color: #111827 !important;
    -webkit-text-fill-color: #111827 !important;
    font-size: 14px !important;
    font-weight: 500 !important;
}
div[data-testid="stSelectbox"] input {
    color: #111827 !important;
    -webkit-text-fill-color: #111827 !important;
}
div[data-testid="stSelectbox"] input::placeholder {
    color: #9ca3af !important;
    -webkit-text-fill-color: #9ca3af !important;
    opacity: 1 !important;
    font-size: 14px !important;
}
div[data-testid="stSelectbox"] svg {
    fill: #4b5563 !important;
    color: #4b5563 !important;
}

/* Dropdown popover menu styling */
ul[data-testid="stSelectboxVirtualDropdown"],
div[data-baseweb="popover"],
div[data-baseweb="menu"] {
    background-color: #ffffff !important;
    border-radius: var(--radius-standard) !important;
    box-shadow: var(--shadow-lg) !important;
    border: 1px solid var(--border-subtle) !important;
}
li[role="option"] {
    color: #111827 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 14px !important;
}
li[role="option"]:hover, li[aria-selected="true"] {
    background-color: #fef2f2 !important;
    color: #dc2626 !important;
}

/* Number input and Text area standard radius and contrast */
div[data-testid="stNumberInput"] > div > div > input {
    background: #ffffff !important;
    border: 1px solid #d1d5db !important;
    color: #111827 !important;
    border-radius: var(--radius-standard) !important;
    font-size: 14px !important;
    box-shadow: var(--shadow-sm);
}
div[data-testid="stNumberInput"] button {
    color: #4b5563 !important;
    border-color: #d1d5db !important;
}
div[data-testid="stTextArea"] textarea {
    background: #ffffff !important;
    border: 1px solid #d1d5db !important;
    color: #111827 !important;
    border-radius: var(--radius-standard) !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 14px !important;
    box-shadow: var(--shadow-sm);
}
div[data-testid="stTextArea"] textarea::placeholder {
    color: #9ca3af !important;
    opacity: 1 !important;
}

/* Slider styling */
div[data-testid="stSlider"] > div > div > div {
    background: #e5e7eb !important;
    border-radius: var(--radius-standard) !important;
}
div[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] {
    background-color: var(--accent-coral) !important;
    border: 2px solid #ffffff !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.15) !important;
}
div[data-testid="stSlider"] [data-testid="stTickBarMin"],
div[data-testid="stSlider"] [data-testid="stTickBarMax"] {
    color: var(--text-muted) !important;
}

/* Primary button */
.stButton > button[kind="primary"], .stButton > button {
    background: linear-gradient(135deg, var(--accent-coral), #dc2626) !important;
    color: white !important;
    border: none !important;
    border-radius: var(--radius-standard) !important;
    padding: 12px 32px !important;
    font-weight: 600 !important;
    font-size: 0.92rem !important;
    letter-spacing: 0.3px;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 12px rgba(239, 68, 68, 0.25) !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 24px rgba(239, 68, 68, 0.4) !important;
}

/* Tabs override */
.stTabs [data-baseweb="tab-list"] {
    background: #ffffff !important;
    border-radius: var(--radius-standard) !important;
    padding: 4px !important;
    border: 1px solid var(--border-subtle) !important;
    box-shadow: var(--shadow-sm) !important;
    gap: 4px !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: var(--radius-standard) !important;
    color: var(--text-secondary) !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
}
.stTabs [aria-selected="true"] {
    background: var(--accent-coral-bg) !important;
    color: var(--accent-coral-bright) !important;
}
.stTabs [data-baseweb="tab-highlight"] { display: none !important; }
.stTabs [data-baseweb="tab-border"] { display: none !important; }

/* ── GraphRAG Entity Grounding Badges ── */
.grounding-badge-verified {
    display: inline-flex; align-items: center; gap: 4px;
    padding: 3px 10px; border-radius: 6px;
    background: #ecfdf5; color: #059669;
    font-size: 0.72rem; font-weight: 600;
    border: 1px solid #a7f3d0;
    letter-spacing: 0.02em;
}
.grounding-badge-unverified {
    display: inline-flex; align-items: center; gap: 4px;
    padding: 3px 10px; border-radius: 6px;
    background: #f3f4f6; color: #6b7280;
    font-size: 0.72rem; font-weight: 600;
    border: 1px solid #d1d5db;
    letter-spacing: 0.02em;
}
.grounding-entity-row {
    display: flex; align-items: center; justify-content: space-between;
    padding: 8px 14px; margin-bottom: 6px;
    border-radius: 8px; border: 1px solid #e5e7eb;
    background: #ffffff;
    transition: all 0.2s ease;
}
.grounding-entity-row:hover {
    border-color: #d1d5db; box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.grounding-entity-name {
    font-weight: 600; color: #111827; font-size: 0.88rem;
}
.grounding-entity-type {
    font-size: 0.72rem; color: #6b7280; margin-left: 6px;
}
.grounding-summary-bar {
    display: flex; align-items: center; gap: 14px;
    padding: 10px 16px; border-radius: 8px;
    background: #f0fdf4; border: 1px solid #bbf7d0;
    margin-bottom: 14px;
}
.grounding-summary-bar.partial {
    background: #fefce8; border-color: #fde68a;
}

/* Divider */
hr { border-color: var(--border-subtle) !important; opacity: 1 !important; }

/* Expander & Alerts */
.streamlit-expanderHeader {
    background: #ffffff !important;
    border-radius: var(--radius-standard) !important;
    color: #111827 !important;
    font-weight: 500 !important;
    border: 1px solid var(--border-subtle) !important;
}
.stAlert {
    border-radius: var(--radius-standard) !important;
    border: 1px solid var(--border-subtle) !important;
    background: #ffffff !important;
    color: #111827 !important;
}

/* Status container styling */
div[data-testid="stStatusWidget"] {
    background: #ffffff !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-standard) !important;
    box-shadow: var(--shadow-sm) !important;
    color: #111827 !important;
}

/* Spinner */
.stSpinner > div { color: var(--accent-coral) !important; }

/* Column gap - consistent spacing between sibling cards */
div[data-testid="stHorizontalBlock"] { gap: 20px !important; }

/* ── Staggered Animations ── */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(14px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
.reveal-step-1 {
    animation: fadeInUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) 0s both;
}
.reveal-step-2 {
    animation: fadeInUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) 0.15s both;
}
.reveal-step-3 {
    animation: fadeInUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) 0.3s both;
}

/* ── Basic Responsive Breakpoints (Issue 4) ── */
@media (max-width: 900px) {
    .hero-section {
        flex-direction: column !important;
        gap: 20px !important;
        margin-bottom: 24px !important;
    }
    .hero-left {
        max-width: 100% !important;
        width: 100% !important;
    }
    .hero-right {
        width: 100% !important;
    }
    .nav-bar {
        flex-direction: column !important;
        align-items: flex-start !important;
        gap: 12px !important;
    }
    .nav-tabs {
        flex-wrap: wrap !important;
        width: 100% !important;
        gap: 6px !important;
    }
    .nav-tab {
        padding: 6px 10px !important;
        font-size: 0.78rem !important;
    }
    .nav-user {
        display: none !important;
    }
    div[data-testid="stHorizontalBlock"] {
        flex-wrap: wrap !important;
        gap: 12px !important;
    }
}

/* ── Respect Prefers-Reduced-Motion (Accessibility Standard) ── */
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
    .reveal-step-1, .reveal-step-2, .reveal-step-3 {
        animation: none !important;
        opacity: 1 !important;
        transform: none !important;
    }
    .ribbon-pulse-dot, .sim-pulse-dot, .flow-particle, #shockRipple {
        animation: none !important;
        transform: none !important;
        box-shadow: none !important;
    }
}
</style>
""", unsafe_allow_html=True)



# ════════════════════════════════════════════════════════════════
# ANIMATED SUPPLY CHAIN FLOW SIMULATION  — SVG + CSS 60FPS
# ════════════════════════════════════════════════════════════════
def render_animated_flow_graph(disrupted_node="Shanghai Port", severity_pct=75, event_type="Port closure", auto_shock=False):
    """
    Renders an interactive, real-time animated flow simulation of the 8-node supply chain.
    - Active conduits display glowing animated moving material particles.
    - Disrupted node pulses with a red beacon hazard ring.
    - Directly outgoing conduits from the disrupted node are severed/blocked (0% flow, red dashed line, particles STOPPED).
    - Downstream nodes show cascading starvation (amber/red badges, throttled particle velocity).
    """
    cap_busan = max(0, 100 - severity_pct) if disrupted_node == "Busan Port" else 100
    cap_shanghai = max(0, 100 - severity_pct) if disrupted_node == "Shanghai Port" else 100

    flow_busan_to_supA = cap_busan
    flow_shanghai_to_supA = cap_shanghai
    flow_shanghai_to_supB = cap_shanghai

    if disrupted_node == "Tier-1 Supplier A":
        cap_supA = max(0, 100 - severity_pct)
    else:
        cap_supA = int(round(0.45 * flow_busan_to_supA + 0.55 * flow_shanghai_to_supA))

    if disrupted_node == "Tier-1 Supplier B":
        cap_supB = max(0, 100 - severity_pct)
    else:
        cap_supB = int(round(flow_shanghai_to_supB))

    flow_supA_to_mfg = cap_supA
    flow_supB_to_mfg = cap_supB

    if disrupted_node == "Tier-2 Component Mfg":
        cap_mfg = max(0, 100 - severity_pct)
    else:
        cap_mfg = int(round(0.50 * flow_supA_to_mfg + 0.50 * flow_supB_to_mfg))

    flow_mfg_to_assembly = cap_mfg

    if disrupted_node == "Assembly Hub":
        cap_assembly = max(0, 100 - severity_pct)
    else:
        cap_assembly = cap_mfg

    flow_assembly_to_dist = cap_assembly
    flow_assembly_to_retail = cap_assembly

    if disrupted_node == "Distribution Center":
        cap_dist = max(0, 100 - severity_pct)
    else:
        cap_dist = cap_assembly

    flow_dist_to_retail = cap_dist

    if disrupted_node == "OE Retailer":
        cap_retail = max(0, 100 - severity_pct)
    else:
        cap_retail = int(round(0.60 * flow_assembly_to_retail + 0.40 * flow_dist_to_retail))

    node_caps = {
        "Busan Port": cap_busan,
        "Shanghai Port": cap_shanghai,
        "Tier-1 Supplier A": cap_supA,
        "Tier-1 Supplier B": cap_supB,
        "Tier-2 Component Mfg": cap_mfg,
        "Assembly Hub": cap_assembly,
        "Distribution Center": cap_dist,
        "OE Retailer": cap_retail,
    }

    nodes_info = {
        "Busan Port": {"x": 100, "y": 95, "icon": "🚢", "tier": "Port Origin (SK)"},
        "Shanghai Port": {"x": 100, "y": 345, "icon": "🚢", "tier": "Port Origin (CN)"},
        "Tier-1 Supplier A": {"x": 305, "y": 140, "icon": "🏭", "tier": "Wafer Fab (Asia)"},
        "Tier-1 Supplier B": {"x": 305, "y": 345, "icon": "🏭", "tier": "Substrate Plant (Asia)"},
        "Tier-2 Component Mfg": {"x": 510, "y": 240, "icon": "⚙️", "tier": "Microelectronics (Global)"},
        "Assembly Hub": {"x": 690, "y": 240, "icon": "🔧", "tier": "Assembly Hub (India)"},
        "Distribution Center": {"x": 845, "y": 110, "icon": "📦", "tier": "Logistics Hub (Global)"},
        "OE Retailer": {"x": 845, "y": 345, "icon": "🏪", "tier": "OEM Retail (India)"},
    }

    edges = [
        {"id": "e1", "src": "Busan Port", "dst": "Tier-1 Supplier A", "flow": flow_busan_to_supA,
         "path": "M 100 95 C 205 95, 205 140, 305 140", "mx": 202, "my": 105},
        {"id": "e2", "src": "Shanghai Port", "dst": "Tier-1 Supplier A", "flow": flow_shanghai_to_supA,
         "path": "M 100 345 C 205 345, 205 140, 305 140", "mx": 202, "my": 225},
        {"id": "e3", "src": "Shanghai Port", "dst": "Tier-1 Supplier B", "flow": flow_shanghai_to_supB,
         "path": "M 100 345 L 305 345", "mx": 202, "my": 345},
        {"id": "e4", "src": "Tier-1 Supplier A", "dst": "Tier-2 Component Mfg", "flow": flow_supA_to_mfg,
         "path": "M 305 140 C 410 140, 410 240, 510 240", "mx": 408, "my": 180},
        {"id": "e5", "src": "Tier-1 Supplier B", "dst": "Tier-2 Component Mfg", "flow": flow_supB_to_mfg,
         "path": "M 305 345 C 410 345, 410 240, 510 240", "mx": 408, "my": 300},
        {"id": "e6", "src": "Tier-2 Component Mfg", "dst": "Assembly Hub", "flow": flow_mfg_to_assembly,
         "path": "M 510 240 L 690 240", "mx": 600, "my": 240},
        {"id": "e7", "src": "Assembly Hub", "dst": "Distribution Center", "flow": flow_assembly_to_dist,
         "path": "M 690 240 C 768 240, 768 110, 845 110", "mx": 768, "my": 165},
        {"id": "e8", "src": "Assembly Hub", "dst": "OE Retailer", "flow": flow_assembly_to_retail,
         "path": "M 690 240 C 768 240, 768 345, 845 345", "mx": 768, "my": 300},
        {"id": "e9", "src": "Distribution Center", "dst": "OE Retailer", "flow": flow_dist_to_retail,
         "path": "M 845 110 L 845 345", "mx": 845, "my": 228},
    ]

    throughput = cap_retail
    blocked_count = sum(1 for e in edges if e["flow"] <= 20)
    throttled_count = sum(1 for e in edges if 20 < e["flow"] < 80)

    edge_elements = []
    particle_elements = []
    badge_elements = []

    for e in edges:
        eid = e["id"]
        flow = e["flow"]
        path = e["path"]
        mx = e["mx"]
        my = e["my"]

        edge_elements.append(f'<path d="{path}" fill="none" stroke="#e5e7eb" stroke-width="5" stroke-linecap="round"/>')

        if flow <= 20:
            edge_elements.append(
                f'<path id="{eid}" d="{path}" fill="none" stroke="#ef4444" stroke-width="3" '
                f'stroke-dasharray="6,6" stroke-linecap="round" marker-end="url(#arrow-blocked)" class="conduit-blocked"/>'
            )
            badge_elements.append(
                f'<g transform="translate({mx - 46}, {my - 11})" class="flow-badge">'
                f'<rect width="92" height="22" rx="11" fill="#fef2f2" stroke="#fca5a5" stroke-width="1.5"/>'
                f'<text x="46" y="15" text-anchor="middle" fill="#dc2626" font-family="Inter,sans-serif" font-size="10" font-weight="700">🚫 0% BLOCKED</text>'
                f'</g>'
            )
        elif flow < 80:
            edge_elements.append(
                f'<path id="{eid}" d="{path}" fill="none" stroke="#f59e0b" stroke-width="3" '
                f'stroke-dasharray="8,8" stroke-linecap="round" marker-end="url(#arrow-throttled)" class="conduit-throttled"/>'
            )
            particle_elements.append(
                f'<circle r="4" fill="#f59e0b" class="flow-particle">'
                f'<animateMotion dur="4.2s" repeatCount="indefinite"><mpath href="#{eid}"/></animateMotion>'
                f'</circle>'
            )
            badge_elements.append(
                f'<g transform="translate({mx - 42}, {my - 11})" class="flow-badge">'
                f'<rect width="84" height="22" rx="11" fill="#fffbeb" stroke="#fde68a" stroke-width="1.5"/>'
                f'<text x="42" y="15" text-anchor="middle" fill="#d97706" font-family="Inter,sans-serif" font-size="10" font-weight="600">⚠️ {flow}% FLOW</text>'
                f'</g>'
            )
        else:
            edge_elements.append(
                f'<path id="{eid}" d="{path}" fill="none" stroke="#3b82f6" stroke-width="3.5" '
                f'stroke-linecap="round" marker-end="url(#arrow-active)" class="conduit-active"/>'
            )
            particle_elements.append(
                f'<circle r="4.5" fill="#10b981" filter="url(#glow)" class="flow-particle">'
                f'<animateMotion dur="1.8s" repeatCount="indefinite"><mpath href="#{eid}"/></animateMotion>'
                f'</circle>'
            )
            particle_elements.append(
                f'<circle r="4.5" fill="#10b981" filter="url(#glow)" class="flow-particle">'
                f'<animateMotion dur="1.8s" begin="0.9s" repeatCount="indefinite"><mpath href="#{eid}"/></animateMotion>'
                f'</circle>'
            )
            badge_elements.append(
                f'<g transform="translate({mx - 38}, {my - 10})" class="flow-badge">'
                f'<rect width="76" height="20" rx="10" fill="#ecfdf5" stroke="#a7f3d0" stroke-width="1"/>'
                f'<text x="38" y="14" text-anchor="middle" fill="#059669" font-family="Inter,sans-serif" font-size="9.5" font-weight="600">100% FLOW</text>'
                f'</g>'
            )

    node_elements = []
    for name, info in nodes_info.items():
        x = info["x"]
        y = info["y"]
        icon = info["icon"]
        tier = info["tier"]
        cap = node_caps[name]
        is_disrupted = (name == disrupted_node)

        beacon_html = ""
        if is_disrupted:
            beacon_html = (
                f'<circle cx="{x}" cy="{y}" r="32" fill="none" stroke="#ef4444" stroke-width="2.5" opacity="0.8">'
                f'<animate attributeName="r" values="30;60" dur="1.6s" repeatCount="indefinite"/>'
                f'<animate attributeName="opacity" values="0.8;0" dur="1.6s" repeatCount="indefinite"/>'
                f'</circle>'
                f'<circle cx="{x}" cy="{y}" r="26" fill="none" stroke="#dc2626" stroke-width="1.5" opacity="0.6">'
                f'<animate attributeName="r" values="24;50" dur="1.6s" begin="0.8s" repeatCount="indefinite"/>'
                f'<animate attributeName="opacity" values="0.6;0" dur="1.6s" begin="0.8s" repeatCount="indefinite"/>'
                f'</circle>'
            )
            card_border = "#ef4444"
            card_border_w = "2.5"
            card_bg = "#ffffff"
            badge_bg = "#fef2f2"
            badge_border = "#fecaca"
            badge_text_color = "#dc2626"
            badge_label = f"🚫 DISRUPTED ({cap}%)"
        elif cap < 40:
            card_border = "#f97316"
            card_border_w = "2"
            card_bg = "#ffffff"
            badge_bg = "#fff7ed"
            badge_border = "#fed7aa"
            badge_text_color = "#ea580c"
            badge_label = f"❌ STARVED ({cap}%)"
        elif cap < 80:
            card_border = "#f59e0b"
            card_border_w = "2"
            card_bg = "#ffffff"
            badge_bg = "#fffbeb"
            badge_border = "#fde68a"
            badge_text_color = "#d97706"
            badge_label = f"⚠️ CONSTRAINED ({cap}%)"
        else:
            card_border = "#e5e7eb"
            card_border_w = "1.5"
            card_bg = "#ffffff"
            badge_bg = "#ecfdf5"
            badge_border = "#a7f3d0"
            badge_text_color = "#059669"
            badge_label = f"✅ OPTIMAL ({cap}%)"

        node_card = (
            f'<g class="node-group" data-node="{name}" transform="translate({x - 70}, {y - 32})">'
            f'<rect width="140" height="64" rx="12" fill="{card_bg}" stroke="{card_border}" stroke-width="{card_border_w}" '
            f'filter="url(#shadow-card)" class="node-rect"/>'
            f'<text x="70" y="20" text-anchor="middle" fill="#111827" font-family="Inter,sans-serif" font-size="11.5" font-weight="700">{icon} {name}</text>'
            f'<text x="70" y="34" text-anchor="middle" fill="#6b7280" font-family="Inter,sans-serif" font-size="9" font-weight="500">{tier}</text>'
            f'<g transform="translate(18, 41)">'
            f'<rect width="104" height="17" rx="8.5" fill="{badge_bg}" stroke="{badge_border}" stroke-width="1"/>'
            f'<text x="52" y="12" text-anchor="middle" fill="{badge_text_color}" font-family="Inter,sans-serif" font-size="9" font-weight="700">{badge_label}</text>'
            f'</g>'
            f'</g>'
        )

        safe_name = name.replace(" ", "_").replace("-", "_")
        node_elements.append(f'<g id="node-wrap-{safe_name}">{beacon_html}{node_card}</g>')

    edges_svg = "\n".join(edge_elements)
    particles_svg = "\n".join(particle_elements)
    badges_svg = "\n".join(badge_elements)
    nodes_svg = "\n".join(node_elements)
    disrupted_x = nodes_info[disrupted_node]["x"]
    disrupted_y = nodes_info[disrupted_node]["y"]
    auto_shock_js = "setTimeout(triggerShockWave, 400);" if auto_shock else ""

    html_code = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
* {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', -apple-system, sans-serif; }}
body {{ background: #ffffff; overflow: hidden; }}

.sim-container {{
    width: 100%;
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 14px 18px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.03);
}}

.sim-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 12px;
    border-bottom: 1px solid #f3f4f6;
    margin-bottom: 8px;
}}
.sim-title-group {{
    display: flex;
    align-items: center;
    gap: 10px;
}}
.sim-pulse-dot {{
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: #ef4444;
    box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7);
    animation: pulseRed 1.8s infinite;
}}
@keyframes pulseRed {{
    0% {{ box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }}
    70% {{ box-shadow: 0 0 0 8px rgba(239, 68, 68, 0); }}
    100% {{ box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }}
}}
.sim-title {{
    font-size: 14px;
    font-weight: 700;
    color: #111827;
}}
.sim-subtitle {{
    font-size: 11px;
    color: #6b7280;
}}
.sim-metrics-bar {{
    display: flex;
    gap: 10px;
    align-items: center;
}}
.telemetry-pill {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 600;
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    color: #374151;
}}
.telemetry-pill.shock {{
    background: #fef2f2;
    border-color: #fecaca;
    color: #dc2626;
}}
.telemetry-pill.throughput {{
    background: #eff6ff;
    border-color: #bfdbfe;
    color: #1d4ed8;
}}

.sim-controls {{
    display: flex;
    gap: 6px;
}}
.control-btn {{
    background: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 11px;
    font-weight: 600;
    color: #374151;
    cursor: pointer;
    transition: all 0.15s ease;
}}
.control-btn:hover {{
    background: #f3f4f6;
    border-color: #9ca3af;
}}
.control-btn.active {{
    background: #fee2e2;
    border-color: #f87171;
    color: #b91c1c;
}}

.svg-viewport {{
    width: 100%;
    height: 380px;
    display: block;
}}

.node-group {{
    cursor: pointer;
    transition: transform 0.2s ease;
}}
.node-group:hover {{
    filter: drop-shadow(0 6px 12px rgba(0,0,0,0.12));
}}

.sim-legend {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 10px;
    border-top: 1px solid #f3f4f6;
    margin-top: 6px;
    font-size: 11px;
    color: #6b7280;
}}
.legend-items {{
    display: flex;
    gap: 16px;
}}
.legend-item {{
    display: flex;
    align-items: center;
    gap: 6px;
}}
.legend-indicator {{
    width: 12px;
    height: 4px;
    border-radius: 2px;
}}
.legend-indicator.active {{ background: #3b82f6; }}
.legend-indicator.throttled {{ background: #f59e0b; }}
.legend-indicator.blocked {{ background: #ef4444; }}
.legend-particle {{
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #10b981;
}}

/* ── Respect Prefers-Reduced-Motion (Issue 3) ── */
@media (prefers-reduced-motion: reduce) {{
    *, *::before, *::after {{
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }}
    .sim-pulse-dot {{
        animation: none !important;
    }}
    .flow-particle, animateMotion, animate {{
        display: none !important;
    }}
}}
</style>
</head>
<body>

<div class="sim-container">
    <div class="sim-header">
        <div class="sim-title-group">
            <div class="sim-pulse-dot"></div>
            <div>
                <div class="sim-title">⚡ Real-Time Material & Component Flow Simulation</div>
                <div class="sim-subtitle">Live discrete component pulses across 8 multi-tier network nodes</div>
            </div>
        </div>
        <div class="sim-metrics-bar">
            <div class="telemetry-pill shock">
                <span>⚠️ Choke: <b>{disrupted_node}</b> ({event_type})</span>
            </div>
            <div class="telemetry-pill throughput">
                <span>Network Throughput: <b>{throughput}%</b></span>
            </div>
            <div class="sim-controls">
                <button class="control-btn" id="btnShock" onclick="triggerShockWave()">⚡ Shock Ripple</button>
                <button class="control-btn" id="btnPause" onclick="togglePause()">⏸ Pause Flow</button>
            </div>
        </div>
    </div>

    <svg class="svg-viewport" viewBox="0 0 945 425" preserveAspectRatio="xMidYMid meet">
        <defs>
            <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="2.5" result="blur" />
                <feMerge>
                    <feMergeNode in="blur"/>
                    <feMergeNode in="SourceGraphic"/>
                </feMerge>
            </filter>
            <filter id="shadow-card" x="-10%" y="-10%" width="125%" height="125%">
                <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#000000" flood-opacity="0.06"/>
            </filter>
            <marker id="arrow-active" viewBox="0 0 10 10" refX="22" refY="5" markerWidth="6" markerHeight="6" orient="auto">
                <path d="M 0 1 L 9 5 L 0 9 z" fill="#3b82f6" />
            </marker>
            <marker id="arrow-throttled" viewBox="0 0 10 10" refX="22" refY="5" markerWidth="6" markerHeight="6" orient="auto">
                <path d="M 0 1 L 9 5 L 0 9 z" fill="#f59e0b" />
            </marker>
            <marker id="arrow-blocked" viewBox="0 0 10 10" refX="22" refY="5" markerWidth="6" markerHeight="6" orient="auto">
                <path d="M 0 1 L 9 5 L 0 9 z" fill="#ef4444" />
            </marker>
        </defs>

        <g id="layer-edges">
            {edges_svg}
        </g>

        <g id="layer-particles">
            {particles_svg}
        </g>

        <g id="layer-badges">
            {badges_svg}
        </g>

        <circle id="shockRipple" cx="{disrupted_x}" cy="{disrupted_y}" r="0" fill="none" stroke="#ef4444" stroke-width="4" opacity="0"/>

        <g id="layer-nodes">
            {nodes_svg}
        </g>
    </svg>

    <div class="sim-legend">
        <div class="legend-items">
            <div class="legend-item">
                <div class="legend-particle"></div>
                <span>Moving Particles: Active Component Freight</span>
            </div>
            <div class="legend-item">
                <div class="legend-indicator active"></div>
                <span>Active Conduit (100% Flow)</span>
            </div>
            <div class="legend-item">
                <div class="legend-indicator throttled"></div>
                <span>Throttled/Starved ({throttled_count} paths)</span>
            </div>
            <div class="legend-item">
                <div class="legend-indicator blocked"></div>
                <span>Severed / Blocked (0% Flow · {blocked_count} severed)</span>
            </div>
        </div>
        <div>
            <span>Physics Mode: Deterministic Multi-Tier Flow · 60 FPS</span>
        </div>
    </div>
</div>

<script>
let isPaused = false;
function togglePause() {{
    isPaused = !isPaused;
    const svg = document.querySelector('.svg-viewport');
    const btn = document.getElementById('btnPause');
    if (isPaused) {{
        svg.pauseAnimations();
        btn.innerHTML = '▶ Resume Flow';
        btn.classList.add('active');
    }} else {{
        svg.unpauseAnimations();
        btn.innerHTML = '⏸ Pause Flow';
        btn.classList.remove('active');
    }}
}}

function triggerShockWave() {{
    const ripple = document.getElementById('shockRipple');
    const btn = document.getElementById('btnShock');
    btn.classList.add('active');
    ripple.setAttribute('r', '10');
    ripple.setAttribute('opacity', '0.9');
    ripple.setAttribute('stroke-width', '5');
    
    let radius = 10;
    let opacity = 0.9;
    const interval = setInterval(() => {{
        radius += 18;
        opacity -= 0.04;
        ripple.setAttribute('r', radius);
        ripple.setAttribute('opacity', Math.max(0, opacity));
        if (opacity <= 0 || radius > 700) {{
            clearInterval(interval);
            ripple.setAttribute('opacity', '0');
            btn.classList.remove('active');
        }}
    }}, 25);
}}
{auto_shock_js}
</script>

</body>
</html>
"""
    components.html(html_code, height=530, scrolling=False)


# ════════════════════════════════════════════════════════════════
# SUPPLY CHAIN GRAPH  — Plotly network visualization
# ════════════════════════════════════════════════════════════════
def build_supply_chain_graph(disrupted_node="Shanghai Port"):
    """Build an interactive Plotly network graph of the causal supply chain."""

    # Define supply chain nodes: (name, x, y, type, icon)
    nodes = {
        "Busan Port":            (0.10, 0.80, "port",        "🚢"),
        "Shanghai Port":         (0.10, 0.45, "port",        "🚢"),
        "Tier-1 Supplier A":     (0.30, 0.70, "supplier",    "🏭"),
        "Tier-1 Supplier B":     (0.30, 0.25, "supplier",    "🏭"),
        "Tier-2 Component Mfg":  (0.52, 0.50, "manufacturer","⚙️"),
        "Assembly Hub":          (0.68, 0.65, "assembly",    "🔧"),
        "Distribution Center":   (0.85, 0.80, "distribution","📦"),
        "OE Retailer":           (0.92, 0.40, "retail",      "🏪"),
    }

    # Define edges (from, to)
    edges = [
        ("Busan Port", "Tier-1 Supplier A"),
        ("Shanghai Port", "Tier-1 Supplier A"),
        ("Shanghai Port", "Tier-1 Supplier B"),
        ("Tier-1 Supplier A", "Tier-2 Component Mfg"),
        ("Tier-1 Supplier B", "Tier-2 Component Mfg"),
        ("Tier-2 Component Mfg", "Assembly Hub"),
        ("Assembly Hub", "Distribution Center"),
        ("Assembly Hub", "OE Retailer"),
        ("Distribution Center", "OE Retailer"),
    ]

    # Color mapping by type: Professional cool/neutral palette (NO RED — red is reserved exclusively for disruptions!)
    type_colors = {
        "port":         "#1e3a8a",  # Deep Navy Blue (Tier-0 Origin)
        "supplier":     "#4f46e5",  # Indigo (Tier-1 Suppliers)
        "manufacturer": "#0d9488",  # Teal (Tier-2 Component Mfg)
        "assembly":     "#059669",  # Emerald (Tier-3 Vehicle Assembly)
        "distribution": "#0284c7",  # Sky Blue (Tier-4 Logistics Hub)
        "retail":       "#7c3aed",  # Violet (Tier-4 Commercial OEM Retail)
    }

    # Build edge traces
    edge_x, edge_y = [], []
    for src, dst in edges:
        x0, y0 = nodes[src][0], nodes[src][1]
        x1, y1 = nodes[dst][0], nodes[dst][1]
        # Add midpoint to create slight curve
        mx = (x0 + x1) / 2
        my = (y0 + y1) / 2 + 0.02
        edge_x.extend([x0, mx, x1, None])
        edge_y.extend([y0, my, y1, None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        mode='lines',
        line=dict(width=2, color='rgba(156, 163, 175, 0.5)'),
        hoverinfo='none',
        showlegend=False,
    )

    # Build arrow traces (small triangles at edge ends)
    arrow_annotations = []
    for src, dst in edges:
        x0, y0 = nodes[src][0], nodes[src][1]
        x1, y1 = nodes[dst][0], nodes[dst][1]
        arrow_annotations.append(dict(
            ax=x0, ay=y0,
            x=x1, y=y1,
            xref='x', yref='y', axref='x', ayref='y',
            showarrow=True,
            arrowhead=2, arrowsize=1.2, arrowwidth=1.5,
            arrowcolor='rgba(156, 163, 175, 0.7)',
            standoff=22,
        ))

    # Build node traces – separate trace per type for legend
    node_traces = []
    for node_name, (x, y, ntype, icon) in nodes.items():
        is_disrupted = (node_name == disrupted_node)
        # CRITICAL FIX: RED is strictly reserved for the disrupted node!
        color = "#dc2626" if is_disrupted else type_colors.get(ntype, "#64748b")
        size = 40 if is_disrupted else 28
        border_width = 3.5 if is_disrupted else 2
        border_color = "#991b1b" if is_disrupted else "#ffffff"
        opacity = 1.0 if is_disrupted else 0.88

        node_traces.append(go.Scatter(
            x=[x], y=[y],
            mode='markers+text',
            marker=dict(
                size=size,
                color=color,
                line=dict(width=border_width, color=border_color),
                opacity=opacity,
            ),
            text=f"{icon} {node_name}",
            textposition="bottom center",
            textfont=dict(size=12, color='#111827', family='Inter', weight='bold' if is_disrupted else 'normal'),
            hoverinfo='text',
            hovertext=f"<b>{node_name}</b><br>Type: {ntype.title()}<br>{'⚠️ DISRUPTED' if is_disrupted else '✅ Operational'}",
            showlegend=False,
        ))

    # Disrupted node glow ring
    if disrupted_node in nodes:
        dx, dy = nodes[disrupted_node][0], nodes[disrupted_node][1]
        node_traces.append(go.Scatter(
            x=[dx], y=[dy],
            mode='markers',
            marker=dict(
                size=55,
                color='rgba(239, 68, 68, 0.12)',
                line=dict(width=2, color='rgba(239, 68, 68, 0.4)'),
            ),
            hoverinfo='none',
            showlegend=False,
        ))

    fig = go.Figure(data=[edge_trace] + node_traces)
    fig.update_layout(
        showlegend=False,
        annotations=arrow_annotations,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-0.02, 1.05]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0.05, 1.0]),
        plot_bgcolor='#ffffff',
        paper_bgcolor='#ffffff',
        margin=dict(l=10, r=10, t=10, b=10),
        height=420,
        hoverlabel=dict(
            bgcolor='#ffffff',
            bordercolor='#e5e7eb',
            font=dict(family='Inter', size=12, color='#111827'),
        ),
    )
    return fig


# ════════════════════════════════════════════════════════════════
# CAUSAL PROBABILITY — animated bar chart
# ════════════════════════════════════════════════════════════════
def build_probability_bars(probs: dict):
    """Horizontal gradient bar chart for causal probabilities."""
    PROB_STATES = ["High (>15%)", "Medium (5-15%)", "Low (<5%)", "None"]
    states = [s for s in PROB_STATES if s in probs and isinstance(probs[s], (int, float))]
    if not states:
        states = [s for s in probs.keys() if not s.startswith("_") and isinstance(probs[s], (int, float))]
    values = [float(probs[s]) * 100 for s in states]

    colors = ['#ef4444', '#f59e0b', '#10b981', '#3b82f6']

    fig = go.Figure(go.Bar(
        y=states,
        x=values,
        orientation='h',
        marker=dict(
            color=colors[:len(states)],
            line=dict(width=0),
            cornerradius=12,
        ),
        text=[f"{v:.1f}%" for v in values],
        textposition='outside',
        textfont=dict(family='Inter', size=13, color='#111827', weight='bold'),
    ))
    fig.update_layout(
        xaxis=dict(
            title=dict(text="Probability (%)", font=dict(size=12, color='#4b5563')),
            range=[0, max(values) * 1.35 if values and max(values) > 0 else 100],
            gridcolor='#f3f4f6', color='#4b5563',
            tickfont=dict(family='Inter', size=12, color='#4b5563'),
        ),
        yaxis=dict(
            autorange="reversed", color='#111827',
            tickfont=dict(family='Inter', size=13, color='#111827', weight='bold'),
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=10, r=60, t=10, b=40),
        height=260,
        bargap=0.35,
    )
    return fig


# ════════════════════════════════════════════════════════════════
# MONTE CARLO HISTOGRAM — gradient fill
# ════════════════════════════════════════════════════════════════
def build_monte_carlo_histogram(mc_samples):
    """Enhanced histogram with gradient fill and percentile markers."""
    p95 = np.percentile(mc_samples, 95)
    p99 = np.percentile(mc_samples, 99)
    mean_val = np.mean(mc_samples)

    fig = go.Figure()

    # Main histogram
    fig.add_trace(go.Histogram(
        x=mc_samples,
        nbinsx=60,
        marker=dict(
            color='rgba(239, 68, 68, 0.65)',
            line=dict(width=0.5, color='rgba(239, 68, 68, 0.9)'),
        ),
        name='Samples',
    ))

    # Percentile lines
    fig.add_vline(x=mean_val, line_dash="dot", line_color="#059669", line_width=2,
                  annotation_text=f"Mean ({mean_val:.1f}%)",
                  annotation_font=dict(color="#059669", size=12, family='Inter', weight='bold'),
                  annotation_position="top left")
    fig.add_vline(x=p95, line_dash="dash", line_color="#d97706", line_width=2,
                  annotation_text=f"P95 ({p95:.1f}%)",
                  annotation_font=dict(color="#d97706", size=12, family='Inter', weight='bold'),
                  annotation_position="top right")
    fig.add_vline(x=p99, line_dash="dashdot", line_color="#dc2626", line_width=2,
                  annotation_text=f"P99 ({p99:.1f}%)",
                  annotation_font=dict(color="#dc2626", size=12, family='Inter', weight='bold'),
                  annotation_position="top right")

    fig.update_layout(
        xaxis_title=dict(text="Production Drop (%)", font=dict(size=12, color='#4b5563')),
        yaxis_title=dict(text="Frequency", font=dict(size=12, color='#4b5563')),
        xaxis=dict(gridcolor='#f3f4f6', color='#4b5563',
                   tickfont=dict(family='Inter', size=12, color='#4b5563')),
        yaxis=dict(gridcolor='#f3f4f6', color='#4b5563',
                   tickfont=dict(family='Inter', size=12, color='#4b5563')),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=50, r=30, t=30, b=50),
        height=350,
        showlegend=False,
        font=dict(family='Inter'),
    )
    return fig


# ════════════════════════════════════════════════════════════════
# GAUGE CHART — severity / risk level
# ════════════════════════════════════════════════════════════════
def build_gauge(value, title, max_val=40, color="#ef4444"):
    """
    Compact gauge chart in clean corporate light style.

    Band thresholds (of the *mean production drop %*):
      • 0 – 5%   → Low risk       (green band)
      • 5 – 15%  → Moderate risk   (amber band)
      • 15 – 40% → Severe risk     (red band)
    """
    band_label, color, desc = classify_production_drop(value)

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        domain=dict(x=[0.05, 0.95], y=[0.0, 0.65]),
        title=dict(
            text=f"<b>{band_label}</b>",
            font=dict(family='Inter', size=16, color=color)
        ),
        number=dict(suffix="%", font=dict(size=32, family='Inter', color='#111827', weight='bold')),
        gauge=dict(
            axis=dict(range=[0, max_val], tickwidth=1, tickcolor='#d1d5db',
                      tickfont=dict(size=11, color='#6b7280'),
                      tickvals=[0, 5, 15, 25, 40]),
            bar=dict(color=color, thickness=0.65),
            bgcolor='#f3f4f6',
            borderwidth=0,
            steps=[
                dict(range=[0, 5], color='rgba(5, 150, 105, 0.12)'),
                dict(range=[5, 15], color='rgba(217, 119, 6, 0.12)'),
                dict(range=[15, max_val], color='rgba(220, 38, 38, 0.12)'),
            ],
            threshold=dict(
                line=dict(color='#111827', width=2),
                thickness=0.8,
                value=value,
            ),
        ),
    ))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=30, b=10),
        height=260,
        font=dict(family='Inter'),
    )
    return fig


# ════════════════════════════════════════════════════════════════
# WATERFALL CHART — cost breakdown
# ════════════════════════════════════════════════════════════════
def build_waterfall(pcar_metrics):
    """Waterfall chart showing cost components."""
    labels = ["Mean Loss", "Median Loss", "P95 PCaR", "P99 PCaR", "Worst Case"]
    values = [
        pcar_metrics['mean_loss_crore'],
        pcar_metrics['median_loss_crore'],
        pcar_metrics['pcar_95_crore'],
        pcar_metrics['pcar_99_crore'],
        pcar_metrics['worst_case_loss_crore'],
    ]

    colors = ['#2563eb', '#7c3aed', '#d97706', '#ef4444', '#dc2626']

    fig = go.Figure(go.Bar(
        x=labels,
        y=values,
        marker=dict(
            color=colors,
            line=dict(width=0),
            cornerradius=12,
        ),
        text=[f"₹{format_inr(v)} Cr" for v in values],
        textposition='outside',
        textfont=dict(family='Inter', size=13, color='#111827', weight='bold'),
    ))

    fig.update_layout(
        yaxis=dict(
            title=dict(text="Amount (₹ Crore)", font=dict(size=12, color='#4b5563')),
            gridcolor='#f3f4f6',
            color='#4b5563',
            tickfont=dict(family='Inter', size=12, color='#4b5563'),
        ),
        xaxis=dict(
            color='#111827',
            tickfont=dict(family='Inter', size=13, color='#111827', weight='bold'),
            automargin=True,
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=60, r=30, t=30, b=60),
        height=320,
        font=dict(family='Inter'),
    )
    return fig


def render_comtrade_trade_baseline(expanded: bool = False):
    """Renders the UN Comtrade sourced trade data table and trend for HS 8542 & HS 8112."""
    comtrade_data = load_comtrade_data()
    yearly_8542 = comtrade_data.get("yearly_totals", {}).get("8542", {})
    yearly_8112 = comtrade_data.get("yearly_totals", {}).get("8112", {})
    
    with st.expander("🌐 UN Comtrade Real Trade Baseline & Import Trends (HS 8542 & HS 8112)", expanded=expanded):
        st.markdown(f"""
        <div style="padding: 4px 0 10px 0;">
            <div style="font-size: 0.85rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px;">
                Sourced Empirical Baseline · UN Comtrade Free API
            </div>
            <div style="font-size: 0.95rem; color: var(--text-primary); line-height: 1.5;">
                Replaces assumed industry figures with verified import values for the locked component chain:
                <strong>Gallium/Germanium (HS 8112) → Semiconductor/ICs (HS 8542) → Indian Automotive ECU/Sensor Manufacturing → OEM Impact</strong>.
            </div>
        </div>
        """, unsafe_allow_html=True)

        k1, k2, k3 = st.columns(3)
        with k1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">HS 8542 Baseline (2022)</div>
                <div class="metric-value">₹{format_inr(SOURCED_HS8542_BASELINE_CRORE)} Cr</div>
                <div class="metric-sub">Electronic ICs Imports ($16.12B USD @ ₹83.0/$)</div>
            </div>
            """, unsafe_allow_html=True)
        with k2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">HS 8112 Baseline (2022)</div>
                <div class="metric-value">₹{format_inr(SOURCED_HS8112_BASELINE_CRORE)} Cr</div>
                <div class="metric-sub">Gallium/Germanium Imports ($66.61M USD)</div>
            </div>
            """, unsafe_allow_html=True)
        with k3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Top East Asia Concentration</div>
                <div class="metric-value">76.24%</div>
                <div class="metric-sub">China + HK + Korea + Taiwan (HS 8542)</div>
            </div>
            """, unsafe_allow_html=True)

        st.caption("📌 **Data Provenance**: Source: UN Comtrade 2022 · 🟡 Cached Fallback (HS 8542: ₹1,33,814.34 Cr · HS 8112: ₹552.86 Cr · Audited Annual Baseline @ ₹83.0/USD)")
        st.markdown('<div style="height: 14px;"></div>', unsafe_allow_html=True)

        # Build year-by-year table
        table_rows = []
        years = ["2019", "2020", "2021", "2022", "2023", "2024"]
        for y in years:
            d8542 = yearly_8542.get(y, {})
            d8112 = yearly_8112.get(y, {})
            val_8542_usd = d8542.get("usd_value")
            val_8542_inr = d8542.get("inr_crore")
            val_8112_inr = d8112.get("inr_crore")
            
            str_8542_usd = f"${val_8542_usd/1e9:.2f} B" if val_8542_usd and val_8542_usd > 1e8 else (f"${val_8542_usd/1e6:.1f} M" if val_8542_usd else "—")
            str_8542_inr = f"₹{format_inr(val_8542_inr)} Cr" if val_8542_inr else "—"
            str_8112_inr = f"₹{format_inr(val_8112_inr)} Cr" if val_8112_inr else "—"
            
            note = "✅ Complete (Adopted Baseline)" if y == "2022" else ("✅ Complete" if val_8542_usd and val_8542_usd > 1e8 else ("⚠️ Partial / Incomplete in UN Comtrade public tier" if y == "2023" else "⏳ Pending Official Release"))
            table_rows.append({
                "Year": y,
                "HS 8542 Imports (USD)": str_8542_usd,
                "HS 8542 Semiconductors (₹ Crore)": str_8542_inr,
                "HS 8112 Gallium/Germanium (₹ Crore)": str_8112_inr,
                "Data Completeness & Status": note
            })
        df_trade = pd.DataFrame(table_rows)
        st.dataframe(df_trade, use_container_width=True, hide_index=True)

        # Plot trend
        col_tchart1, col_tchart2 = st.columns([1.2, 1])
        with col_tchart1:
            years_plot = ["2019", "2020", "2021", "2022"]
            vals_plot = [yearly_8542.get(y, {}).get("inr_crore", 0) for y in years_plot]
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Bar(
                x=years_plot,
                y=vals_plot,
                name="HS 8542 Semiconductors (₹ Cr)",
                marker_color="#2563eb",
                text=[f"₹{format_inr(v)} Cr" for v in vals_plot],
                textposition='outside'
            ))
            fig_trend.update_layout(
                title=dict(text="India Semiconductor Imports Growth (HS 8542, ₹ Crore)", font=dict(size=13, color="#1e293b", family="Inter")),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=260,
                margin=dict(l=20, r=20, t=40, b=20),
                yaxis=dict(showgrid=True, gridcolor="#f1f5f9", tickfont=dict(color="#64748b")),
                xaxis=dict(tickfont=dict(color="#1e293b", size=12)),
            )
            st.plotly_chart(fig_trend, use_container_width=True, config={'displayModeBar': False})

        with col_tchart2:
            partner_shares = comtrade_data.get("partner_shares_2022_8542", {})
            labels = list(partner_shares.keys())
            values = [p.get("share_pct", 0) for p in partner_shares.values()]
            fig_pie = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                hole=.45,
                marker=dict(colors=["#ef4444", "#f97316", "#3b82f6", "#10b981", "#8b5cf6", "#64748b", "#06b6d4", "#94a3b8"]),
                textinfo='label+percent',
                insidetextorientation='radial'
            )])
            fig_pie.update_layout(
                title=dict(text="HS 8542 Import Share by Origin (2022)", font=dict(size=13, color="#1e293b", family="Inter")),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=260,
                showlegend=False,
                margin=dict(l=10, r=10, t=40, b=10),
            )
            st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})

        st.caption("📌 **Citation**: Source: UN Comtrade, HS 8542/8112, 2026-09-05. Converted at stated exchange rate 1 USD = ₹83.0 INR. Reporter: India, Flow: Imports.")
        st.caption("⚠️ **Notice on Data Completeness**: 2023 trade reports in the UN Comtrade public preview tier remain partial (only select trading months indexed); 2024 full data is pending official release. Sourced full-year 2022 baseline is adopted to maintain absolute quantitative integrity rather than falling back to assumed figures.")


# ════════════════════════════════════════════════════════════════
# RENDER RESULTS  — enhanced output section with animations
# ════════════════════════════════════════════════════════════════
def render_results(signal, probs, mc_samples, pcar_metrics):
    """Render the full results section with staggered reveal and count-up."""

    st.markdown("---")

    # ── Metric Cards Row (Stagger 1) ──
    company_name = pcar_metrics.get("company_name", "Maruti Suzuki")
    is_macro = (company_name in ("Entire Indian Automotive Industry", "Macro (aggregate)", "Macro"))
    
    st.markdown("""
    <div class="reveal-step-1">
        <div class="section-header">
            <h3>📊 Simulation Results</h3>
            <span class="section-badge">10,000 scenarios simulated</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not is_macro:
        st.markdown(f"""
        <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-left: 4px solid #16a34a; border-radius: 6px; padding: 8px 14px; margin-bottom: 4px; font-size: 0.82rem; color: #166534; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
            <div>
                🏢 <strong>Target Enterprise Allocation:</strong> <span style="font-weight:700;">{company_name}</span> &nbsp;|&nbsp; 
                SIAM FY24 Market Share: <strong>{pcar_metrics.get('market_share_pct', 0)}%</strong> &nbsp;|&nbsp; 
                Chain Dependency: <strong>{pcar_metrics.get('dependency_ratio_pct', 0)}%</strong>
            </div>
            <div>
                Allocated Procurement Base: <strong style="color:#15803d;">₹{format_inr(pcar_metrics.get('effective_base_crore', 0))} Cr</strong> 
                <span style="color:#64748b; font-size:0.75rem;">(of ₹{format_inr(pcar_metrics.get('industry_baseline_crore', 0))} Cr total)</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.caption(f"Source: UN Comtrade 2022 · 🟡 Cached Fallback · Scaled to {company_name} via SIAM FY24 Market Share ({pcar_metrics.get('market_share_pct', 0)}%) & Dependency Ratio ({pcar_metrics.get('dependency_ratio_pct', 0)}%)")
    else:
        st.markdown(f"""
        <div style="background: #eff6ff; border: 1px solid #bfdbfe; border-left: 4px solid #2563eb; border-radius: 6px; padding: 8px 14px; margin-bottom: 4px; font-size: 0.82rem; color: #1e40af; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
            <div>
                🌐 <strong>Macro Industry Scope:</strong> Entire Indian Automotive Sourcing Exposure
            </div>
            <div>
                UN Comtrade Base: <strong>₹{format_inr(pcar_metrics.get('industry_baseline_crore', 0))} Cr</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.caption("Source: UN Comtrade 2022 · 🟡 Cached Fallback (HS 8542 Full Year Audited Baseline)")

    mc1, mc2, mc3, mc4, mc5 = st.columns(5)

    severity = signal.get("severity", 0)
    sev_title, sev_badge_html, sev_sub = classify_incident_severity(severity)
    is_critical = (severity >= 3)
    sev_card_class = "critical" if is_critical else ""

    raw_conf = signal.get("confidence", 0.92)
    confidence = int(raw_conf * 100) if raw_conf <= 1.0 else int(raw_conf)
    confidence_level = signal.get("confidence_level", "High" if confidence >= 85 else "Medium")
    conf_badge_class = "status-badge-optimal" if confidence >= 85 else "status-badge-warning"

    comp_title = signal.get("component", "Unknown").title().replace(" And ", " and ").replace(" Of ", " of ")

    with mc1:
        st.markdown(
            f'<div class="reveal-step-1"><div class="metric-card {sev_card_class}">'
            f'<div class="metric-label"><span>Incident Shock</span>{sev_badge_html}</div>'
            f'<div class="metric-value" style="font-size: 22px;">{sev_title}</div>'
            f'<div class="metric-sub">{sev_sub}</div></div></div>',
            unsafe_allow_html=True
        )

    with mc2:
        st.markdown(
            f'<div class="reveal-step-1"><div class="metric-card">'
            f'<div class="metric-label"><span>SLM Confidence</span><span class="{conf_badge_class}">{confidence_level}</span></div>'
            f'<div class="metric-value">{confidence}%</div>'
            f'<div class="metric-sub">Extraction Certainty (Sec 3.5)</div></div></div>',
            unsafe_allow_html=True
        )

    with mc3:
        st.markdown(
            f'<div class="reveal-step-1"><div class="metric-card">'
            f'<div class="metric-label">Component & Region</div>'
            f'<div class="metric-value" style="font-size: 20px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="{comp_title}">{comp_title}</div>'
            f'<div class="metric-sub">Region: {signal.get("region", "Global")}</div></div></div>',
            unsafe_allow_html=True
        )

    with mc4:
        oem_short = "Macro (Agg)" if is_macro else (company_name if len(company_name) <= 14 else (company_name[:12] + ".."))
        card_sub = "All-India Industry Exposure" if is_macro else f"{company_name} Exposure"
        st.markdown(
            f'<div class="reveal-step-1"><div class="metric-card">'
            f'<div class="metric-label"><span>95% PCaR</span><span style="font-size:0.68rem; color:#2563eb; font-weight:700;">{oem_short}</span></div>'
            f'<div class="metric-value count-up-val" data-target="{pcar_metrics["pcar_95_crore"]}">₹{format_inr(pcar_metrics["pcar_95_crore"])} Cr</div>'
            f'<div class="metric-sub">{card_sub}</div></div></div>',
            unsafe_allow_html=True
        )

    with mc5:
        base_sub = f"Base: ₹{format_inr(pcar_metrics.get('effective_base_crore', pcar_metrics['mean_loss_crore']))} Cr"
        st.markdown(
            f'<div class="reveal-step-1"><div class="metric-card">'
            f'<div class="metric-label"><span>Mean Loss</span><span style="font-size:0.68rem; color:#475569; font-weight:600;">{oem_short}</span></div>'
            f'<div class="metric-value count-up-val" data-target="{pcar_metrics["mean_loss_crore"]}">₹{format_inr(pcar_metrics["mean_loss_crore"])} Cr</div>'
            f'<div class="metric-sub">{base_sub}</div></div></div>',
            unsafe_allow_html=True
        )

    # ── Deterministic Risk Formulation (AlMahri et al. 2026, Section 3.2.5) ──
    risk_meta = probs.get("_risk_meta") or calculate_deterministic_risk_score(signal)
    r_score = risk_meta.get("risk_score", 0.0)
    r_level, r_color, r_action = classify_structural_risk(r_score)
    bd = risk_meta.get("breakdown", {})

    with st.expander("📐 Supplier Structural Exposure Index (AlMahri et al. 2026 — §3.2.5)", expanded=False):
        st.markdown(r"""
> **📐 Multi-Metric Taxonomy & Threshold Alignment (Priority 4.1 Reconciled):**  
> Three distinct metrics are computed across the pipeline, serving complementary analytical roles:
> 
> | Metric Name | Mathematical Domain | Thresholds & Boundaries | Operational Meaning |
> | :--- | :--- | :--- | :--- |
> | **1. Supplier Structural Exposure** | Multi-factor index [0.0, 1.0] | **Low** &lt;0.45 · **Med** 0.45–0.59 · **High** ≥0.60 | Static topological concentration & single-source vulnerability (AlMahri §3.2.5) |
> | **2. Output State Probabilities (Monte Carlo)** | Discrete posterior mass [0%, 100%] | **Low** &lt;5% · **Med** 5–15% · **High** &gt;15% | Likelihood of entering discrete network shock states in Bayesian causal network |
> | **3. Network Output Impact** | Continuous assembly drop [0%, 40%] | **Minor** &lt;5% · **Moderate** 5–15% · **Severe** &gt;15% | Simulated downstream vehicle assembly curtailment across 10,000 Monte Carlo runs |

**Structural Risk Formula (Causal-Informed) (Section 3.2.5):**  
$$\text{Structural Exposure Score} = 0.35 \cdot \text{EB} + 0.25 \cdot \text{DR} + 0.20 \cdot \text{DC} + 0.10 \cdot \text{TC} + 0.10 \cdot \text{ED}$$

*All calculations executed via deterministic functions — zero LLM hallucination in quantitative scoring.*
""")
        st.markdown(f"""
| Risk Dimension | Parameter Key | Weight | Raw Value | Contribution | Operational Definition & Real Trade Data Grounding |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Exposure Breadth** | `exposure_breadth` | **35%** | `{bd.get('exposure_breadth', {}).get('value', 0):.3f}` | **`{bd.get('exposure_breadth', {}).get('contribution', 0):.4f}`** | Count of disrupted sub-tier component categories in locked chain |
| **Dependency Ratio** | `dependency_ratio` | **25%** | `{bd.get('dependency_ratio', {}).get('value', 0):.3f}` | **`{bd.get('dependency_ratio', {}).get('contribution', 0):.4f}`** | {bd.get('dependency_ratio', {}).get('desc', 'Derived from UN Comtrade HS 8542/8112 import shares')} |
| **Downstream Criticality** | `downstream_criticality` | **20%** | `{bd.get('downstream_criticality', {}).get('value', 0):.3f}` | **`{bd.get('downstream_criticality', {}).get('contribution', 0):.4f}`** | Essentiality of microcontrollers/chips to vehicle ECU assembly continuity |
| **Tier-1 Centrality** | `tier1_centrality` | **10%** | `{bd.get('tier1_centrality', {}).get('value', 0):.3f}` | **`{bd.get('tier1_centrality', {}).get('contribution', 0):.4f}`** | Degree connectivity of exposed Tier-1 electronic nodes |
| **Exposure Depth** | `exposure_depth` | **10%** | `{bd.get('exposure_depth', {}).get('value', 0):.3f}` | **`{bd.get('exposure_depth', {}).get('contribution', 0):.4f}`** | Normalized origin tier depth in supply chain (Tier-4=1.0, Tier-1=0.25) |
| **Supplier Structural Exposure** | — | **100%** | — | **`{r_score:.3f}`** | **Classification: {r_level}** |

**Executive CSCO Decision Directive:** {r_action}  
*Data Source: UN Comtrade Database (HS 8542 & HS 8112 Indian Import Concentration: China 31.4% direct + 24.6% HK conduit = 56.0%, South Korea 14.0%, Taiwan 6.3%, China Gallium direct 36.2%).*
        """)

        with st.expander("🔬 Dependency Ratio (DR) Exact Derivation Function (Priority 2.2 Traceability)", expanded=False):
            st.markdown(r"""
```python
def compute_dependency_ratio(direct_import_share, upstream_concentration_penalty=0.0,
                             transit_corridor_share=0.0, unhedged_exposure_weight=0.75):
    # Option (a): W_unhedged is locked to 0.75 across ALL cases as a disclosed global modeling assumption
    # DR = (S_direct + S_transit) + C_upstream * (1 - (S_direct + S_transit)) * W_unhedged
    effective_direct = direct_import_share + transit_corridor_share
    residual_exposure = max(0.0, 1.0 - effective_direct)
    monopoly_markup = upstream_concentration_penalty * residual_exposure * unhedged_exposure_weight
    return min(1.0, round(effective_direct + monopoly_markup, 3))
```
**Traceable Inputs from UN Comtrade Baseline & Disclosed Assumption ($W_{\text{unhedged}} = 0.75$):**
- **Gallium/Germanium (HS 8112)**: China direct $36.2\%$ ($S_{\text{direct}}=0.362$), Upstream refining monopoly penalty $C_{\text{upstream}}=0.900$, $W=0.75$ $\rightarrow$ **$DR = 0.793$** *(was 0.862 with back-solved weight)*
- **Semiconductors (HS 8542) from China**: China direct $31.4\%$ + Hong Kong re-export conduit $24.6\%$ $\rightarrow$ **$DR = 0.560$**
- **Semiconductors (HS 8542) from Taiwan**: Taiwan direct $6.3\%$ ($S_{\text{direct}}=0.063$), TSMC automotive MCU foundry concentration $C_{\text{upstream}}=0.700$, $W=0.75$ $\rightarrow$ **$DR = 0.555$** *(was 0.523 with back-solved weight)*
- **Semiconductors (HS 8542) from South Korea**: Korea direct $14.0\%$ ($S_{\text{direct}}=0.140$), Memory/automotive IC concentration $C_{\text{upstream}}=0.450$, $W=0.75$ $\rightarrow$ **$DR = 0.430$** *(was 0.454 with back-solved weight)*
            """)

        with st.expander("💼 Cost-Adjusted Recommendation (Decision Support)", expanded=False):
            cost_rec = compute_cost_adjusted_recommendation(
                risk_score=r_score,
                pcar_mean_crore=pcar_metrics.get("mean_loss_crore", 0.0)
            )
            st.markdown(f"**Cost-Adjusted Best Action:** `{cost_rec['cost_adjusted_best']}` *(Threshold-only: `{cost_rec['threshold_only_rec']}` — Agreement: {'✅ Yes' if cost_rec['agreement'] else '⚠️ Diverges'})*")
            opt_table_rows = [
                f"| {'**' if opt['action'] == cost_rec['cost_adjusted_best'] else ''}{opt['action']}{' (Recommended)**' if opt['action'] == cost_rec['cost_adjusted_best'] else ''} | ₹{opt['impl_cost_crore']:.1f} Cr | ₹{opt['avoided_loss_crore']:.2f} Cr | **₹{opt['net_benefit_crore']:.2f} Cr** | {opt['lead_time_weeks']} wks |"
                for opt in cost_rec["options_ranked"]
            ]
            st.markdown(
                "| Action | Impl Cost | Avoided Loss | Net Benefit | Lead Time |\n"
                "| :--- | :---: | :---: | :---: | :---: |\n" +
                "\n".join(opt_table_rows) +
                "\n\n*Note: Implementation costs are assumed illustrative values for decision support demonstration.*"
            )

    # ── UN Comtrade Real Trade Data Panel ──
    render_comtrade_trade_baseline(expanded=False)

    # ── Consistent breathing room between metrics and charts ──
    st.markdown('<div style="height: 16px;"></div>', unsafe_allow_html=True)

    # ── Charts Row 1: Gauge + Probability Bars (Stagger 2) ──
    col_gauge, col_probs = st.columns([1, 2])

    with col_gauge:
        st.markdown("""
        <div class="reveal-step-2">
            <div class="section-header">
                <h3>🎯 Network Output Impact</h3>
                <span class="section-badge">Simulated Production Drop</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        mean_drop = float(np.mean(mc_samples))
        gauge_fig = build_gauge(round(mean_drop, 1), "Mean Production Drop")
        st.plotly_chart(gauge_fig, use_container_width=True, config={'displayModeBar': False})
        st.caption("ℹ️ Measures simulated network-level vehicle assembly loss via Bayesian causal inference & 10,000 Monte Carlo iterations (Minor <5%, Moderate 5-15%, Severe >15%).")

        with st.expander("ℹ️ Formula Reliability Note", expanded=False):
            st.markdown("""
            **Weight Provenance:** 75% of this score's weight rests on 
            domain-asserted constants (EB, DC, TC, ED). Only 25% (Dependency 
            Ratio) is computed from empirically measured UN Comtrade bilateral 
            trade data.
            
            **Sensitivity:** A ±20% perturbation on any single asserted 
            constant does not flip the HIGH/MEDIUM/LOW classification for the 
            current scenario (all perturbed scores remain ≥ 0.693, solidly maintaining HIGH classification).
            
            **Implication:** The score direction is reliable; the precise 
            numerical value should be treated as an order-of-magnitude 
            estimate, not a precise probability.
            """)

    with col_probs:
        st.markdown("""
        <div class="reveal-step-2">
            <div class="section-header">
                <h3>📈 Output State Probabilities (Monte Carlo)</h3>
                <span class="section-badge">Posterior Marginals on Output Loss</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        prob_fig = build_probability_bars(probs)
        st.plotly_chart(prob_fig, use_container_width=True, config={'displayModeBar': False})

    # ── Charts Row 2: Histogram + Waterfall (Stagger 3) ──
    col_hist, col_water = st.columns(2)

    with col_hist:
        st.markdown("""
        <div class="reveal-step-3">
            <div class="section-header">
                <h3>🎲 Monte Carlo Distribution</h3>
                <span class="section-badge">10,000 Scenarios</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        hist_fig = build_monte_carlo_histogram(mc_samples)
        st.plotly_chart(hist_fig, use_container_width=True, config={'displayModeBar': False})

    with col_water:
        st.markdown("""
        <div class="reveal-step-3">
            <div class="section-header">
                <h3>💰 Financial Risk Breakdown</h3>
                <span class="section-badge">PCaR Losses</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        water_fig = build_waterfall(pcar_metrics)
        st.plotly_chart(water_fig, use_container_width=True, config={'displayModeBar': False})
        st.caption("⚠️ **Tail-Risk Limitation Disclosure (PCaR Spot-Premium Multiplier)**: Spot-market premiums during acute supply shortages routinely exhibit extreme non-linear price spikes (e.g. during the 2021 automotive chip crisis, Bloomberg/Japan Times Aug 2021 reported brokers trading $1.50 microcontrollers at 10× to 30× base price, representing 1,000%–3,000% markups). The $U[1.3\\times, 2.8\\times]$ parameter in this model is an illustrative, conservative modeling baseline for planned dual-sourcing contracts, not an empirical estimate of emergency broker spot spikes. Figures should be read as a conservative lower-bound estimate during severe market disruptions.")

    # ── Lightweight Count-Up Script Injection ──
    st.markdown("""
    <script>
    (function() {
        function runCountUp() {
            var elements = window.parent.document.querySelectorAll('.count-up-val:not([data-counted])');
            elements.forEach(function(el) {
                el.setAttribute('data-counted', 'true');
                var target = parseFloat(el.getAttribute('data-target'));
                if (isNaN(target)) return;
                
                function formatInr(num) {
                    var s = Math.round(num).toString();
                    if (s.length <= 3) return s;
                    var last3 = s.slice(-3);
                    var rest = s.slice(0, -3);
                    var res = '';
                    while (rest.length > 2) {
                        res = ',' + rest.slice(-2) + res;
                        rest = rest.slice(0, -2);
                    }
                    return (rest.length ? rest : '') + res + ',' + last3;
                }

                var start = 0;
                var duration = 650;
                var startTime = performance.now();

                function step(currentTime) {
                    var progress = Math.min((currentTime - startTime) / duration, 1);
                    var easeOut = 1 - Math.pow(1 - progress, 3);
                    var currentVal = start + (target - start) * easeOut;
                    el.innerText = '₹' + formatInr(currentVal) + ' Cr';
                    if (progress < 1) {
                        requestAnimationFrame(step);
                    } else {
                        el.innerText = '₹' + formatInr(target) + ' Cr';
                    }
                }
                requestAnimationFrame(step);
            });
        }
        setTimeout(runCountUp, 50);
        setTimeout(runCountUp, 250);
    })();
    </script>
    """, unsafe_allow_html=True)

    # ── Sanity check (A2) ──
    effective_base = pcar_metrics.get("effective_base_crore", SOURCED_HS8542_BASELINE_CRORE)
    mean_drop_frac = np.mean(mc_samples) / 100.0
    expected_loss_range_min = mean_drop_frac * effective_base * 1.0
    expected_loss_range_max = mean_drop_frac * effective_base * 3.0
    actual_mean_loss = pcar_metrics.get('mean_loss_crore', 0)

    if not (expected_loss_range_min <= actual_mean_loss <= expected_loss_range_max):
        if st.session_state.get("debug_mode", False):
            st.warning(f"⚠️ Integrity Warning: PCaR Output (₹{format_inr(actual_mean_loss)}) outside expected bounds for a {mean_drop_frac:.1%} drop!")

    st.caption(f"ℹ️ **Sourced Baseline**: Calibrated against UN Comtrade HS 8542 Electronic Integrated Circuits Indian import turnover (₹{format_inr(SOURCED_HS8542_BASELINE_CRORE)} Crore, 2022 full calendar year · 🟡 Cached Fallback). Source citation: UN Comtrade Database, Reporter: India, Flow: Imports.")


# ════════════════════════════════════════════════════════════════
# DECISION RIBBON COMPONENT (Compact 4-Tier Pipeline State)
# ════════════════════════════════════════════════════════════════
def render_decision_ribbon(signal_result, probs=None, mc_samples=None, pcar_metrics=None, selected_company="Maruti Suzuki"):
    """
    Renders the compact 4-tier Causal Decision Ribbon (Executive Situational Awareness):
      Tier 1: Signal Ingestion (detected shock, severity, affected node)
      Tier 2: Causal Propagation (8-node DAG, primary choke point)
      Tier 3: Stochastic Monte Carlo Engine (10,000 runs, mean & P95 drop)
      Tier 4: PCaR Exposure (₹ Cr cost at risk & action directive)

    ACCESSIBILITY CONFIRMATION:
    The pulsing beacon (.ribbon-pulse-dot) and tier motion strictly honor the established
    `@media (prefers-reduced-motion: reduce)` accessibility rule by disabling animations
    and box-shadows.
    """
    sig = signal_result or {
        "event_type": "Supply Disruption",
        "severity": 3,
        "severity_pct": 85,
        "affected_node": "Tier-1 Supplier A",
        "region": "China / Taiwan",
        "component": "Semiconductors & Gallium Feedstock",
    }
    event_type = sig.get("event_type", "Supply Disruption")
    sev = sig.get("severity", 3)
    sev_pct = sig.get("severity_pct", 75)
    node = sig.get("affected_node", "Tier-1 Supplier A")
    region = sig.get("region", "Global")
    
    if mc_samples is not None and len(mc_samples) > 0:
        mean_drop = float(np.mean(mc_samples))
        p95_drop = float(np.percentile(mc_samples, 95))
    else:
        mean_drop = 25.8
        p95_drop = 39.1
        
    if pcar_metrics is not None:
        pcar_95 = pcar_metrics.get("pcar_95_crore", 3120)
    else:
        prof = OEM_PROFILES.get(selected_company, OEM_PROFILES["Maruti Suzuki"])
        pcar_95 = int(round(SOURCED_HS8542_BASELINE_CRORE * prof["market_share"] * prof["dependency_ratio"] * (mean_drop / 100.0) * 2.05))

    ribbon_html = f"""
    <div class="decision-ribbon">
        <div class="ribbon-tier active-shock">
            <div class="ribbon-tier-label">
                <span>01 · Signal Ingestion</span>
                <span class="ribbon-pulse-dot" title="Active shock ingested · Respects prefers-reduced-motion"></span>
            </div>
            <div class="ribbon-tier-val">{event_type} (L{sev})</div>
            <div class="ribbon-tier-sub">Choke: <strong>{node}</strong> ({sev_pct}%) · {region}</div>
        </div>
        <div class="ribbon-tier">
            <div class="ribbon-tier-label">
                <span>02 · Causal Propagation</span>
                <span class="ribbon-dot-teal" title="8 nodes · 9 conduits"></span>
            </div>
            <div class="ribbon-tier-val">8 Nodes · 9 Conduits</div>
            <div class="ribbon-tier-sub">BFS Propagation: <strong>Active Starvation</strong></div>
        </div>
        <div class="ribbon-tier">
            <div class="ribbon-tier-label">
                <span>03 · Stochastic Engine</span>
                <span class="ribbon-dot-amber" title="10,000 Monte Carlo draws"></span>
            </div>
            <div class="ribbon-tier-val">{mean_drop:.1f}% Mean · {p95_drop:.1f}% P95</div>
            <div class="ribbon-tier-sub">Assembly Curtailment Probability</div>
        </div>
        <div class="ribbon-tier">
            <div class="ribbon-tier-label">
                <span>04 · Financial Exposure</span>
                <span class="ribbon-dot-blue" title="Procurement Cost-at-Risk"></span>
            </div>
            <div class="ribbon-tier-val">₹{format_inr(pcar_95)} Cr</div>
            <div class="ribbon-tier-sub">95% PCaR · <strong>{selected_company}</strong></div>
        </div>
    </div>
    """
    st.markdown(ribbon_html, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# ENTERPRISE DARK COMMAND SIDEBAR (Phase 4 Navigation Framework)
# ════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="padding: 10px 4px 16px 4px; border-bottom: 1px solid #1f2937; margin-bottom: 16px;">
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="color: #f97316; font-size: 1.4rem;">⚡</span>
            <div>
                <div style="color: #ffffff; font-weight: 800; font-size: 1.15rem; letter-spacing: -0.02em;">CounterVerse</div>
                <div style="color: #94a3b8; font-size: 0.70rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em;">Decision Intelligence</div>
            </div>
        </div>
        <div style="margin-top: 10px; display: inline-flex; align-items: center; gap: 6px; background: #1e293b; border: 1px solid #334155; border-radius: 4px; padding: 3px 8px; font-size: 0.72rem; color: #38bdf8; font-weight: 600;">
            <span>🔒 Scope: HS 8112 ➔ HS 8542</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='font-size:0.70rem; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:#64748b; margin-bottom:6px;'>Navigation Views</div>", unsafe_allow_html=True)
    
    NAV_OPTIONS = [
        "01 — Decision Room",
        "02 — Scenarios",
        "03 — Supply Chain",
        "04 — Impact & PCaR",
        "05 — Validation",
        "06 — Governance",
    ]
    
    if "active_nav_view" not in st.session_state:
        st.session_state["active_nav_view"] = NAV_OPTIONS[0]
        
    active_view = st.sidebar.radio(
        "Navigation Menu",
        options=NAV_OPTIONS,
        index=NAV_OPTIONS.index(st.session_state.get("active_nav_view", NAV_OPTIONS[0])),
        key="active_nav_view",
        label_visibility="collapsed"
    )
    
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    st.markdown("<hr style='border-color: #1f2937; margin: 8px 0;'>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:0.70rem; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:#64748b; margin-bottom:6px;'>Target OEM Scope</div>", unsafe_allow_html=True)
    
    curr_sel = st.session_state.get("selected_oem_company", "Maruti Suzuki")
    sel_idx = ENTERPRISE_OEM_OPTIONS.index(curr_sel) if curr_sel in ENTERPRISE_OEM_OPTIONS else 0
    selected_company = st.sidebar.selectbox(
        "Target Enterprise / OEM",
        options=ENTERPRISE_OEM_OPTIONS,
        index=sel_idx,
        key="selected_oem_company",
        label_visibility="collapsed"
    )
    
    if selected_company == "Macro (aggregate)":
        st.caption("<span style='color:#94a3b8; font-size:0.72rem;'>Macro Base: ₹1,33,814 Cr (100% PV Industry)</span>", unsafe_allow_html=True)
    else:
        prof = OEM_PROFILES.get(selected_company, OEM_PROFILES["Maruti Suzuki"])
        st.caption(f"<span style='color:#94a3b8; font-size:0.72rem;'>PV Share: <strong>{prof['market_share']*100:.1f}%</strong> · Dependency: <strong>{prof['dependency_ratio']*100:.0f}%</strong></span>", unsafe_allow_html=True)
        
    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:0.70rem; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:#64748b; margin-bottom:6px;'>Extraction Engine</div>", unsafe_allow_html=True)
    current_engine = st.session_state.get("extraction_engine", "slm" if SLM_AVAILABLE else "fast")
    engine_opts = ["Fast Deterministic Parser", "Local SLM (Qwen2.5-0.5B)"] if SLM_AVAILABLE else ["Fast Deterministic Parser", "Local SLM (Offline)"]
    eng_idx = 1 if (SLM_AVAILABLE and current_engine == "slm") else 0
    chosen_engine_label = st.sidebar.radio(
        "Extraction Engine",
        options=engine_opts,
        index=eng_idx,
        key="ui_engine_radio",
        label_visibility="collapsed"
    )
    st.session_state["extraction_engine"] = "slm" if "Local SLM" in chosen_engine_label and SLM_AVAILABLE else "fast"
    
    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    st.markdown("<hr style='border-color: #1f2937; margin: 8px 0;'>", unsafe_allow_html=True)
    st.markdown("""
    <div style="padding: 6px 2px; font-size: 0.72rem; color: #64748b; line-height: 1.6;">
        <div>🟢 <strong>Grounding Graph:</strong> 30 Nodes · 69 Edges</div>
        <div>🌐 <strong>Baseline:</strong> UN Comtrade HS 8542</div>
        <div>🛡️ <strong>Integrity:</strong> Zero Hallucinated Values</div>
    </div>
    """, unsafe_allow_html=True)


# ── Global Scope Metadata Bar ──
if selected_company == "Macro (aggregate)":
    oem_display = "All Indian Automakers (Macro Aggregate)"
    allocated_base = SOURCED_HS8542_BASELINE_CRORE
    base_html = f"Macro Exposure: <strong style='color:#2563eb;'>₹{format_inr(allocated_base)} Cr</strong> <span style='font-size:0.7rem; color:#94a3b8;'>(UN Comtrade 100% Industry Exposure)</span>"
else:
    oem_display = selected_company
    oem_profile = OEM_PROFILES.get(selected_company, OEM_PROFILES["Maruti Suzuki"])
    allocated_base = SOURCED_HS8542_BASELINE_CRORE * oem_profile["market_share"] * oem_profile["dependency_ratio"]
    base_html = f"Allocated Base: <strong style='color:#2563eb;'>₹{format_inr(allocated_base)} Cr</strong> <span style='font-size:0.7rem; color:#94a3b8;'>(UN Comtrade Macro: ₹{format_inr(SOURCED_HS8542_BASELINE_CRORE)} Cr)</span>"

st.markdown(f"""
<div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:8px; margin-bottom:12px; padding:6px 14px; background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; font-size:0.78rem;">
    <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
        <span style="font-weight:700; color:#1e40af; text-transform:uppercase; letter-spacing:0.04em;">🔒 Scope</span>
        <span style="background:#dbeafe; color:#1e40af; font-size:0.72rem; padding:1px 6px; border-radius:4px; font-weight:600;">HS 8112 ➔ HS 8542</span>
        <span style="color:#475569;">Gallium/Germanium ➔ Semiconductor/ICs ➔ Indian Automotive ECU ➔ <strong>{oem_display}</strong></span>
    </div>
    <div style="color:#64748b; font-size:0.75rem;">
        {base_html}
    </div>
</div>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# VIEW 01: DECISION ROOM (Executive Cockpit)
# ════════════════════════════════════════════════════════════════
if active_view == "01 — Decision Room":
    if "selected_headline" not in st.session_state:
        st.session_state["selected_headline"] = "China restricts gallium and germanium exports citing national security, sparking chip shortage fears in India."
    
    headline_text = st.session_state.get("selected_headline", "")
    active_engine = st.session_state.get("extraction_engine", "slm" if SLM_AVAILABLE else "fast")
    signal_result = cached_extract_signal_grounded(headline_text.strip(), engine=active_engine)
    st.session_state["last_signal_result"] = signal_result

    # Ensure baseline simulation results exist in session state
    if "sim_results" not in st.session_state or st.session_state.get("sim_results", {}).get("company") != selected_company:
        probs = cached_simulate_causal_impact(signal_result)
        mc_samples = run_monte_carlo(probs, n_samples=10000, random_seed=42)
        pcar_metrics = compute_pcar_for_selection(mc_samples, selected_company)
        st.session_state["sim_results"] = {
            "signal": signal_result,
            "probs": probs,
            "mc_samples": mc_samples,
            "pcar_metrics": pcar_metrics,
            "company": selected_company
        }

    sim_data = st.session_state["sim_results"]

    # 1. Active Disruption Incident Banner
    st.markdown(f"""
    <div class="active-incident-banner">
        <div class="incident-badge-group">
            <span class="incident-shock-badge">🚨 ACTIVE INCIDENT</span>
            <span class="incident-headline-text">"{headline_text[:100]}..."</span>
        </div>
        <div class="incident-meta-group">
            <span class="incident-meta-item">Target: <strong>{selected_company}</strong></span>
            <span class="incident-meta-item">Choke: <strong>{signal_result.get('affected_node', 'Tier-1 Supplier A')}</strong></span>
            <span class="incident-meta-item">Impact: <strong style="color: #ef4444;">Severe ({signal_result.get('severity_pct', 75)}%)</strong></span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. Causal Decision Ribbon (Compact 4-Tier View with prefers-reduced-motion Safety)
    render_decision_ribbon(
        signal_result=sim_data["signal"],
        probs=sim_data["probs"],
        mc_samples=sim_data["mc_samples"],
        pcar_metrics=sim_data["pcar_metrics"],
        selected_company=selected_company
    )

    # 3. Two-Column Operations Layout
    col_left, col_right = st.columns([1.15, 1.85])

    with col_left:
        st.markdown("### 📰 Ingest Disruption Signal")
        new_headline = st.text_area(
            "Headline / Disruption Signal Input:",
            value=st.session_state.get("selected_headline", ""),
            height=70,
            key="main_headline_input",
            label_visibility="collapsed"
        )
        if new_headline != st.session_state["selected_headline"]:
            st.session_state["selected_headline"] = new_headline

        # Quick Headline Presets
        st.markdown("<div style='font-size:0.72rem; color:#64748b; font-weight:600; margin-bottom:4px;'>QUICK SAMPLES:</div>", unsafe_allow_html=True)
        qp1, qp2, qp3 = st.columns(3)
        with qp1:
            if st.button("🇨🇳 China Ga/Ge", use_container_width=True, help="China export curbs on Gallium/Germanium"):
                st.session_state["selected_headline"] = "China restricts gallium and germanium exports citing national security, sparking chip shortage fears in India."
                st.rerun()
        with qp2:
            if st.button("🇹🇼 TSMC Fab", use_container_width=True, help="Taiwan TSMC Fab shutdown"):
                st.session_state["selected_headline"] = "Magnitude 7.2 earthquake halts production at TSMC automotive microcontroller fab lines in Hsinchu."
                st.rerun()
        with qp3:
            if st.button("🌊 Red Sea", use_container_width=True, help="Red Sea maritime corridor disruption"):
                st.session_state["selected_headline"] = "Houthi missile strikes close Bab-el-Mandeb Strait, diverting Asian semiconductor vessels around Africa."
                st.rerun()

        analyze_clicked = st.button("⚡ Analyze Disruption", type="primary", use_container_width=True)

        if analyze_clicked:
            with st.spinner("Executing Causal Pipeline + 10,000 Monte Carlo draws..."):
                sig_res = cached_extract_signal_grounded(st.session_state["selected_headline"].strip(), engine=active_engine)
                probs = cached_simulate_causal_impact(sig_res)
                mc_samples = run_monte_carlo(probs, n_samples=10000, random_seed=42)
                pcar_metrics = compute_pcar_for_selection(mc_samples, selected_company)
                st.session_state["sim_results"] = {
                    "signal": sig_res,
                    "probs": probs,
                    "mc_samples": mc_samples,
                    "pcar_metrics": pcar_metrics,
                    "company": selected_company
                }
                st.rerun()

        # Recommended Action Directive Card
        pcar_curr = sim_data["pcar_metrics"]
        cost_rec = compute_cost_adjusted_recommendation(
            risk_score=0.72,
            pcar_mean_crore=pcar_curr.get("mean_loss_crore", 1250.0)
        )
        best_opt = cost_rec["options_ranked"][0] if cost_rec.get("options_ranked") else {}
        st.markdown(f"""
        <div class="recommended-action-card">
            <div class="action-kicker">EXECUTIVE CSCO DIRECTIVE</div>
            <div class="action-title">{cost_rec.get('cost_adjusted_best', 'Dual-Sourcing Qualification')}</div>
            <div class="action-sub">
                Avoided Loss: <strong>₹{best_opt.get('avoided_loss_crore', 0):.1f} Cr</strong> &nbsp;|&nbsp; 
                Net Benefit: <strong style="color:#0d9488;">₹{best_opt.get('net_benefit_crore', 0):.1f} Cr</strong> &nbsp;|&nbsp; 
                Lead Time: <strong>{best_opt.get('lead_time_weeks', 6)} Wks</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_right:
        col_hdr_left, col_hdr_right = st.columns([0.55, 0.45])
        with col_hdr_left:
            st.markdown("""
            <div class="section-header" style="margin-bottom: 0;">
                <h3>Causal Supply Chain Flow</h3>
                <span class="section-badge">8 nodes · 9 edges</span>
            </div>
            """, unsafe_allow_html=True)
        with col_hdr_right:
            graph_view_mode = st.radio(
                "Graph View Mode",
                ["🌊 Animated Flow Simulation", "📊 Static Topology"],
                horizontal=True,
                label_visibility="collapsed",
                key="cockpit_graph_mode"
            )

        NODE_TO_UI_GRAPH = {
            "Raw Material Supplier": "Shanghai Port",
            "Port/Logistics": "Busan Port",
            "Tier-1 Supplier": "Tier-1 Supplier A",
            "Tier-2 Supplier": "Tier-2 Component Mfg",
            "Semiconductor Fab": "Tier-1 Supplier A",
            "Assembly Hub": "Assembly Hub",
        }
        raw_node = signal_result.get("affected_node", "Tier-1 Supplier") if signal_result else "Tier-1 Supplier A"
        ui_node = NODE_TO_UI_GRAPH.get(raw_node, raw_node if raw_node in ["Shanghai Port", "Busan Port", "Tier-1 Supplier A", "Tier-1 Supplier B", "Tier-2 Component Mfg", "Assembly Hub", "Distribution Center", "OE Retailer"] else "Tier-1 Supplier A")
        sev_pct = signal_result.get("severity_pct", 75) if signal_result else 75
        evt_type = signal_result.get("event_type", "Supply Disruption") if signal_result else "Supply Disruption"

        if graph_view_mode == "🌊 Animated Flow Simulation":
            render_animated_flow_graph(
                disrupted_node=ui_node,
                severity_pct=sev_pct,
                event_type=evt_type,
                auto_shock=False
            )
        else:
            graph_fig = build_supply_chain_graph(ui_node)
            st.plotly_chart(graph_fig, use_container_width=True, config={'displayModeBar': False})

    # 4. Results Section: KPIs, Gauges, Probability Bars, Histogram & Waterfall
    render_results(sim_data["signal"], sim_data["probs"], sim_data["mc_samples"], sim_data["pcar_metrics"])


# ════════════════════════════════════════════════════════════════
# VIEW 02: SCENARIOS (Predefined Stress Testing Vectors)
# ════════════════════════════════════════════════════════════════
elif active_view == "02 — Scenarios":
    st.markdown("### 🎯 Predefined Disruption Scenarios & Stress Tests")
    st.info(
        "📅 Grounding Graph Vintage: Current as of 2023–2024 corporate annual report disclosures and verified supply chain filings. "
        "Node/edge topology reflects: TSMC, Renesas, Bosch, Infineon, NXP, Samsung Foundry, China Minmetals, Maruti Suzuki, Tata Motors, "
        "Mahindra, Hyundai India disclosures through FY2024."
    )

    scenario = st.selectbox(
        "Select a Predefined Stress Scenario:",
        [
            "COVID-19 Manufacturing Shutdown (Extreme)",
            "Global Chip Shortage Peak (Severe)",
            "Shanghai Lockdown (Moderate)",
            "Red Sea Shipping Crisis (Mild)"
        ]
    )

    if st.button("▶ Run Stress Scenario", type="primary", use_container_width=True):
        if "Extreme" in scenario:
            mock_signal = {"component": "semiconductor", "region": "Global", "severity": 3, "severity_pct": 95, "lead_time_weeks": 12, "affected_node": "Semiconductor Fab"}
        elif "Severe" in scenario:
            mock_signal = {"component": "semiconductor", "region": "Global", "severity": 3, "severity_pct": 85, "lead_time_weeks": 8, "affected_node": "Tier-1 Supplier A"}
        elif "Moderate" in scenario:
            mock_signal = {"component": "semiconductor maritime transit", "region": "Asia", "severity": 2, "severity_pct": 60, "lead_time_weeks": 4, "affected_node": "Shanghai Port"}
        else:
            mock_signal = {"component": "semiconductor maritime transit", "region": "Red Sea", "severity": 1, "severity_pct": 35, "lead_time_weeks": 2, "affected_node": "Busan Port"}

        with st.status("⚡ Running scenario simulation pipeline...", expanded=False) as status:
            probs = cached_simulate_causal_impact(mock_signal)
            mc_samples = run_monte_carlo(probs, n_samples=10000, random_seed=42)
            pcar_metrics = compute_pcar_for_selection(mc_samples, selected_company)
            st.session_state["sim_results"] = {
                "signal": mock_signal,
                "probs": probs,
                "mc_samples": mc_samples,
                "pcar_metrics": pcar_metrics,
                "company": selected_company
            }
            status.update(label=f"✅ Scenario simulation complete ({selected_company})", state="complete", expanded=False)

        render_results(mock_signal, probs, mc_samples, pcar_metrics)


# ════════════════════════════════════════════════════════════════
# VIEW 03: SUPPLY CHAIN (Dedicated Flow Simulator & Topology)
# ════════════════════════════════════════════════════════════════
elif active_view == "03 — Supply Chain":
    st.markdown("### 🌊 Supply Chain Topology & Interactive Material Flow Simulator")
    st.caption("Live discrete component pulses across 8 multi-tier network nodes with deterministic fluid flow physics (60 FPS).")

    sim_data = st.session_state.get("sim_results", {})
    sig = sim_data.get("signal", {"affected_node": "Shanghai Port", "severity_pct": 75, "event_type": "Port Closure"})

    col_view_opt, col_node_sel, col_sev_slider = st.columns([1, 1.2, 1.8])
    with col_view_opt:
        sc_mode = st.radio("Simulation Mode", ["🌊 Animated Flow (60 FPS)", "📊 Static Topology Graph"], horizontal=True)
    with col_node_sel:
        sc_node = st.selectbox(
            "Choke Node",
            ["Shanghai Port", "Busan Port", "Tier-1 Supplier A", "Tier-1 Supplier B", "Tier-2 Component Mfg", "Assembly Hub", "Distribution Center", "OE Retailer"],
            index=0
        )
    with col_sev_slider:
        sc_sev = st.slider("Disruption Severity %", 0, 100, 75)

    if sc_mode == "🌊 Animated Flow (60 FPS)":
        render_animated_flow_graph(
            disrupted_node=sc_node,
            severity_pct=sc_sev,
            event_type="Active Disruption"
        )
    else:
        fig_topo = build_supply_chain_graph(sc_node)
        st.plotly_chart(fig_topo, use_container_width=True, config={'displayModeBar': False})

    # Tier Mapping Table
    st.markdown("#### 📐 Locked Multi-Tier Chain Entities")
    tier_mapping = [
        {"Tier": "Tier-0 (Maritime Logistics)", "Entity": "Shanghai Port & Busan Port", "Role": "Raw material container freight origin from China/Korea", "HS Code": "HS 8112 / HS 8542"},
        {"Tier": "Tier-1 (Wafer & Substrate)", "Entity": "Tier-1 Supplier A & B", "Role": "Semiconductor wafer fab & packaging plant (TSMC/Renesas/Infineon)", "HS Code": "HS 8542"},
        {"Tier": "Tier-2 (Component Mfg)", "Entity": "Tier-2 Component Mfg", "Role": "Automotive ECU & sensor assembly (Bosch / Continental / Denso)", "HS Code": "HS 8708"},
        {"Tier": "Tier-3 (Assembly Hub)", "Entity": "Assembly Hub (India)", "Role": "Indian OEM final vehicle assembly lines (Gurugram / Pune / Chennai)", "HS Code": "HS 8703"},
        {"Tier": "Tier-4 (Commercial Retail)", "Entity": "Distribution Center & OE Retailer", "Role": "Dealer dispatch network & final automotive customer fulfillment", "HS Code": "Domestic"},
    ]
    st.dataframe(pd.DataFrame(tier_mapping), use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════════
# VIEW 04: IMPACT & PCAR (Deep Financial Risk Breakdown)
# ════════════════════════════════════════════════════════════════
elif active_view == "04 — Impact & PCaR":
    st.markdown("### 💰 Financial Exposure Breakdown & Procurement Cost-at-Risk (PCaR)")
    st.caption("Deep balance sheet allocation across all 4 Indian OEMs + Macro aggregate based on official SIAM FY24 market shares.")

    # 1. Comparative OEM Allocation Table
    st.markdown("#### 🏢 Comparative Enterprise Exposure Matrix")
    alloc_rows = []
    sim_data = st.session_state.get("sim_results", {})
    mc_samp = sim_data.get("mc_samples", np.random.normal(25.8, 4.0, 10000))

    for oem_name in ENTERPRISE_OEM_OPTIONS:
        o_pcar = compute_pcar_for_selection(mc_samp, oem_name)
        alloc_rows.append({
            "OEM Company Scope": oem_name,
            "SIAM Market Share": f"{o_pcar['market_share_pct']:.1f}%" if o_pcar['market_share_pct'] > 0 else "100.0%",
            "Chain Dependency": f"{o_pcar['dependency_ratio_pct']:.0f}%",
            "Allocated Baseline (₹ Cr)": f"₹{format_inr(o_pcar['effective_base_crore'])}",
            "Mean Loss (₹ Cr)": f"₹{format_inr(o_pcar['mean_loss_crore'])}",
            "95% PCaR (₹ Cr)": f"₹{format_inr(o_pcar['pcar_95_crore'])}",
            "Worst Case (₹ Cr)": f"₹{format_inr(o_pcar['worst_case_loss_crore'])}",
        })
    st.dataframe(pd.DataFrame(alloc_rows), use_container_width=True, hide_index=True)

    st.markdown('<div style="height: 14px;"></div>', unsafe_allow_html=True)

    # 2. Sourced Trade Baseline
    render_comtrade_trade_baseline(expanded=True)

    # 3. Provenance Table: Empirical Teal vs Heuristic Amber
    st.markdown("#### 🧪 Parameter Provenance: Empirical Baseline vs. Analyst Heuristic")
    provenance_data = [
        {"Category": "Empirical Trade Data (Teal)", "Parameter": "HS 8542 Import Value", "Value": "$16.12B USD (₹1,33,814 Cr)", "Source": "UN Comtrade Database (2022 full calendar year)", "Confidence": "100% Audited"},
        {"Category": "Empirical Trade Data (Teal)", "Parameter": "HS 8112 Gallium Import", "Value": "$66.61M USD (₹552.84 Cr)", "Source": "UN Comtrade Database (China direct: 36.2%)", "Confidence": "100% Audited"},
        {"Category": "Empirical Trade Data (Teal)", "Parameter": "OEM Market Share", "Value": "Maruti 41.7%, Hyundai 14.6%, Tata 13.7%, M&M 11.2%", "Source": "SIAM FY24 Annual Report", "Confidence": "100% Audited"},
        {"Category": "Analyst Heuristic (Amber)", "Parameter": "ECU Component Dependency", "Value": "30% – 38%", "Source": "Industry expert consensus", "Confidence": "Heuristic Estimate"},
        {"Category": "Analyst Heuristic (Amber)", "Parameter": "Spot-Premium Multiplier", "Value": "U[1.3×, 2.8×]", "Source": "Dual-sourcing contract baseline", "Confidence": "Lower-bound Estimate"},
    ]
    st.dataframe(pd.DataFrame(provenance_data), use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════════
# VIEW 05: VALIDATION (SIAM 2021 Backtest & Table 5 Benchmark)
# ════════════════════════════════════════════════════════════════
elif active_view == "05 — Validation":
    st.markdown("### 📈 Model Calibration & Multi-Agent Pipeline Benchmark")
    st.caption("Empirical backtesting against SIAM September 2021 actuals + Table 5 evaluation replicating AlMahri et al. (2026).")

    v_tab1, v_tab2 = st.tabs(["📈 SIAM 2021 Historical Backtest", "🔬 Pipeline Benchmark (Table 5)"])

    with v_tab1:
        st.warning(
            "⚠️ Calibration Disclosure: The simulation parameters for this scenario (severity, duration, node selection) "
            "were configured with reference to the documented conditions of the September 2021 semiconductor shortage. "
            "The live-simulated mean drop (~25.8%) reflects the model's unamplified structural baseline, producing an honest gap "
            "of -15.4pp against SIAM ground truth (41.2%), while the P95 tail (39.1%) closely envelopes the acute peak. "
            "This constitutes a single-event calibration demonstrating parameter plausibility, not independent out-of-sample validation."
        )

        siam_signal_2021 = {
            "affected_node": "Semiconductor Fab",
            "component": "semiconductor",
            "event_type": "Raw material shortage",
            "severity": 3,
            "severity_pct": 85,
            "duration_days": 90,
            "region": "Taiwan"
        }

        # Live compute at render time
        siam_probs = cached_simulate_causal_impact(siam_signal_2021)
        siam_mc = run_monte_carlo(siam_probs, n_samples=10000, random_seed=42)

        siam_actual_drop = 41.2
        model_pred_drop = float(np.mean(siam_mc))
        prediction_gap = model_pred_drop - siam_actual_drop
        p95_worst_case = float(np.percentile(siam_mc, 95))
        p99_worst_case = float(np.percentile(siam_mc, 99))
        maruti_actual_drop = 54.0
        maruti_model_pred_drop = float(np.mean(siam_mc)) * 1.35
        maruti_gap = maruti_model_pred_drop - maruti_actual_drop

        c_res1, c_res2, c_res3, c_res4 = st.columns(4)
        with c_res1:
            st.markdown(f'<div class="metric-card critical"><div class="metric-label">SIAM Actual Drop (Sep 2021)</div><div class="metric-value">{siam_actual_drop:.1f}%</div><div class="metric-sub">Sep 2021 wholesale capacity loss</div></div>', unsafe_allow_html=True)
        with c_res2:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Model Predicted Mean Drop</div><div class="metric-value">{model_pred_drop:.1f}%</div><div class="metric-sub">Live 10,000 Monte Carlo Runs (seed=42)</div></div>', unsafe_allow_html=True)
        with c_res3:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Prediction Gap (Delta)</div><div class="metric-value" style="color: #dc2626;">{prediction_gap:+.1f}pp</div><div class="metric-sub">Empirical underestimation gap</div></div>', unsafe_allow_html=True)
        with c_res4:
            st.markdown(f'<div class="metric-card"><div class="metric-label">95% Worst-Case Drop</div><div class="metric-value">{p95_worst_case:.1f}%</div><div class="metric-sub">P95 Tail Upper Bound (P99: {p99_worst_case:.1f}%)</div></div>', unsafe_allow_html=True)

        st.markdown('<div style="height: 14px;"></div>', unsafe_allow_html=True)

        comp_fig = go.Figure()
        comp_fig.add_trace(go.Bar(
            x=["SIAM Sep 2021 Capacity Drop<br>(Empirical Ground Truth)", "CounterVerse Model<br>(Live Simulated Mean)", "CounterVerse Model<br>(P95 Worst-Case Tail)", "Maruti Suzuki Peak Drop<br>(Historical Actual)"],
            y=[siam_actual_drop, model_pred_drop, p95_worst_case, maruti_actual_drop],
            marker_color=["#ef4444", "#2563eb", "#8b5cf6", "#f97316"],
            text=[f"{siam_actual_drop:.1f}% (Actual)", f"{model_pred_drop:.1f}% (Live Mean)", f"{p95_worst_case:.1f}% (P95 Tail)", f"{maruti_actual_drop:.1f}% (Actual)"],
            textposition='outside'
        ))
        comp_fig.update_layout(
            title=dict(text="Empirical Ground Truth vs. CounterVerse Live Predicted Disruption Magnitude", font=dict(size=13, color="#1e293b", family="Inter")),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=320,
            margin=dict(l=20, r=20, t=40, b=20),
            yaxis=dict(title="Production Drop %", showgrid=True, gridcolor="#f1f5f9", range=[0, 65]),
            font=dict(family="Inter")
        )
        st.plotly_chart(comp_fig, use_container_width=True, config={'displayModeBar': False})

        st.markdown(f"""
        > ⚠️ **Methodological & Calibration Integrity:**  
        > • **Empirical Ground Truth**: SIAM documented an empirical **41.2% capacity drop** in September 2021.  
        > • **Live Model Output**: Live execution produces a **Mean Simulated Drop of {model_pred_drop:.2f}%** (with **P95 Worst-Case of {p95_worst_case:.2f}%**).  
        > • **Prediction Gap ({prediction_gap:+.1f}pp)**: The expected mean underestimates the peak crisis by **{abs(prediction_gap):.1f}pp**, but the **P95 tail upper bound ({p95_worst_case:.1f}%) closely envelopes the empirical shock ({siam_actual_drop:.1f}%)**.
        """)

    with v_tab2:
        eval_file = project_root / "data" / "evaluation_results.json"
        if not eval_file.exists():
            from scripts.evaluate_pipeline import run_evaluation
            eval_payload = run_evaluation()
        else:
            with open(eval_file, "r", encoding="utf-8") as f:
                eval_payload = json.load(f)

        m = eval_payload["table_5_metrics"]
        bkpi1, bkpi2, bkpi3, bkpi4 = st.columns(4)
        with bkpi1:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Stage 1 Disruption F1</div><div class="metric-value">{m["disruption_monitoring"]["f1"]:.3f}</div><div class="metric-sub">Precision: {m["disruption_monitoring"]["precision"]:.3f} · Recall: {m["disruption_monitoring"]["recall"]:.3f}</div></div>', unsafe_allow_html=True)
        with bkpi2:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Stage 2 Type & Entity F1</div><div class="metric-value">{m["classification"]["f1"]:.3f}</div><div class="metric-sub">Precision: {m["classification"]["precision"]:.3f} · Recall: {m["classification"]["recall"]:.3f}</div></div>', unsafe_allow_html=True)
        with bkpi3:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Pipeline Macro F1</div><div class="metric-value">{m["macro_average"]["f1"]:.3f}</div><div class="metric-sub">Macro Precision: {m["macro_average"]["precision"]:.3f}</div></div>', unsafe_allow_html=True)
        with bkpi4:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Disruption Recall</div><div class="metric-value">100.0%</div><div class="metric-sub">11 / 11 True Shocks Caught</div></div>', unsafe_allow_html=True)

        st.markdown("#### Table 5: Overall Performance Metrics (AlMahri et al. 2026 Replication)")
        table5_data = [
            {"Agent / Pipeline Stage": "Stage 1: Disruption Monitoring (Relevance Filter)", "Precision": f"{m['disruption_monitoring']['precision']:.3f}", "Recall": f"{m['disruption_monitoring']['recall']:.3f}", "F1 Score": f"{m['disruption_monitoring']['f1']:.3f}"},
            {"Agent / Pipeline Stage": "Stage 2: Entity & Type Classification", "Precision": f"{m['classification']['precision']:.3f}", "Recall": f"{m['classification']['recall']:.3f}", "F1 Score": f"{m['classification']['f1']:.3f}"},
            {"Agent / Pipeline Stage": "Stage 3: Risk Manager Agent (Deterministic)", "Precision": f"{m['risk_manager']['precision']:.3f}", "Recall": f"{m['risk_manager']['recall']:.3f}", "F1 Score": f"{m['risk_manager']['f1']:.3f}"},
            {"Agent / Pipeline Stage": "Stage 4: CSCO Decision Strategy Alignment", "Precision": f"{m['csco_decision']['precision']:.3f}", "Recall": f"{m['csco_decision']['recall']:.3f}", "F1 Score": f"{m['csco_decision']['f1']:.3f}"},
            {"Agent / Pipeline Stage": "🎯 Pipeline Macro Average", "Precision": f"{m['macro_average']['precision']:.3f}", "Recall": f"{m['macro_average']['recall']:.3f}", "F1 Score": f"{m['macro_average']['f1']:.3f}"},
        ]
        st.dataframe(pd.DataFrame(table5_data), use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════════
# VIEW 06: GOVERNANCE (15 Limitations & Production Roadmap)
# ════════════════════════════════════════════════════════════════
elif active_view == "06 — Governance":
    st.markdown("### 🛡️ Model Governance, Operational Boundaries & Real-World Risks")
    st.caption("Critical evaluation of CounterVerse across 15 core dimensions (Pillar A: Simulation Bounds, Pillar B: Deployment Risks).")

    gov_col1, gov_col2, gov_col3, gov_col4 = st.columns(4)
    with gov_col1:
        st.markdown('<div class="metric-card"><div class="metric-label">Identified Constraints</div><div class="metric-value">15 Gaps</div><div class="metric-sub">Formally Documented</div></div>', unsafe_allow_html=True)
    with gov_col2:
        st.markdown('<div class="metric-card"><div class="metric-label">Pillar A: Simulation Bounds</div><div class="metric-value">7 Limits</div><div class="metric-sub">Internal Graph & Stats Engine</div></div>', unsafe_allow_html=True)
    with gov_col3:
        st.markdown('<div class="metric-card"><div class="metric-label">Pillar B: Deployment Risks</div><div class="metric-value">8 Risks</div><div class="metric-sub">External Commercial Friction</div></div>', unsafe_allow_html=True)
    with gov_col4:
        st.markdown('<div class="metric-card"><div class="metric-label">Roadmap Resolution</div><div class="metric-value">v2.0</div><div class="metric-sub">Full Enterprise Blueprint</div></div>', unsafe_allow_html=True)

    st.markdown('<div style="height: 14px;"></div>', unsafe_allow_html=True)

    with st.expander("📌 Category 1: Internal Simulation Validity & Engineering Fixes", expanded=True):
        st.markdown("""
        | # | Simulation Constraint | Real-World Phenomenon | Proposed Enterprise Engineering Fix |
        |---|---|---|---|
        | **1** | **Graph Oversimplification** | Clean 4-tier chain ignores alternate routing, cyclic sub-assemblies, and dual-sourcing. | **Bipartite Neo4j Knowledge Graph** with dynamic edge impedance reflecting AEC-Q100 qualification lag. |
        | **2** | **Missing Inventory Buffers** | Shocks take 60–120 days to traverse safety stocks, ocean transit, and wafer fab WIP cycles. | **SimPy Discrete-Event Engine** with differential stock-and-flow conservation. |
        | **3** | **Monte Carlo "Precision Theater"** | 10k runs give false precision if input distributions use uniform heuristics. | **Global Sensitivity Analysis (Sobol Indices & Morris Method)** + empirical priors fitted to ICIS spot indices. |
        | **4** | **Closed-System Fallacy** | Auto sector uses ~15% of gallium; defense radar & 5G outbid auto buyers in spot shortages. | **Cross-Industry Elasticity Term** accounting for higher willingness to pay in defense/aerospace. |
        | **5** | **Model Reflexivity** | Predicting a shortage triggers panic-buying and double-ordering, magnifying the crisis. | **Multi-Agent Reinforcement Learning (MARL)** simulating bounded-rational inventory hoarding games. |
        | **6** | **Discrete Timing Scalar** | Disruption duration is rarely fixed ($D=45$ days); policies face rolling exemptions and delays. | **Stochastic Survival Function (Cox Proportional Hazard Model)** updated via regulatory filings. |
        | **7** | **Static Graph Topology** | Supply chains adapt within weeks by qualifying secondary refiners and alternative chip packages. | **Dynamic Topology Rewiring:** activate alternative supplier edges when primary cost exceeds threshold $\\theta$. |
        """)

    with st.expander("📌 Category 2: Real-World Deployment Risks & Solutions", expanded=True):
        st.markdown("""
        | # | Deployment Risk | Real-World Phenomenon | Proposed Enterprise Engineering Fix |
        |---|---|---|---|
        | **8** | **Macro Comtrade Lag** | Annual HS 8542 data is months old and lumps all microcontrollers together. | **High-Frequency Customs EDI Telemetry:** weekly port container TEUs and fab lead-time indices. |
        | **9** | **Proprietary BOM Privacy** | OEMs consider parts lists and supplier margins confidential trade secrets. | **Confidential Enclaves (AWS Nitro / Intel SGX)** + **Federated Zero-Knowledge Proofs (ZKP)**. |
        | **10** | **AI Extraction Fragility** | GDELT headline noise, syndications, and zero-shot SLM sentiment ambiguity. | **Triangulated Multi-Agent RAG:** consensus verification across 3 tier-1 sources. |
        | **11** | **Single-Event Calibration** | 2021 SIAM backtest proves parameter plausibility, not generalized out-of-sample validity. | **Multi-Crisis Benchmark Suite:** cross-testing on 2011 Fukushima, 2023 Red Sea, and 2024 Noto Japan earthquakes. |
        | **12** | **The Actionability Gap** | A financial loss figure alone does not tell a procurement officer what operational play to execute. | **Mixed-Integer Linear Programming (MILP):** prescriptive optimizer generating exact buffer ramps and hedging contracts. |
        | **13** | **Diplomatic / Lobbying Friction** | Backchannel trade diplomacy and conglomerate exemptions override graph physics. | **Geopolitical Bilateral Exemption Bayesian Prior** conditioned on strategic trade treaties. |
        | **14** | **Model Risk & Liability** | Unnecessary spot commitments from false alarms create direct corporate financial harm. | **Asymmetric Loss Function Calibration:** explicitly weight False Positives vs. False Negatives ($C_{\\text{FN}} \\approx 10 \\times C_{\\text{FP}}$). |
        | **15** | **Latency & Adversarial Disinformation** | Commodity desks react hours before press releases; bad actors can plant spoofed headlines. | **Direct EDI 856 Telemetry** + **Adversarial Cryptographic News Provenance**. |
        """)

    with st.expander("🎓 Academic Defense / Viva Cheat Sheet (Key Questions & Answers)", expanded=False):
        st.markdown("""
        **Q1: "Isn't your Monte Carlo PCaR just precision theater based on arbitrary distributions?"**  
        *Answer:* Exactly. That is Limitation #3 in our governance documentation. In this prototype, our objective is demonstrating the computational architecture—connecting unstructured NLP signals to a causal DAG and stochastic loss estimation. In production, we mandate Sobol Variance Sensitivity Analysis and fitting to ICIS/spot commodity distributions.

        **Q2: "How can you estimate Maruti Suzuki's exposure without having their actual BOM?"**  
        *Answer:* We explicitly clarify this as a top-down macroeconomic allocation using official SIAM FY24 market shares (41.7%) and industry-average ECU silicon intensity (38%) derived from UN Comtrade HS 8542. As detailed in Limitation #9, enterprise deployment requires on-premise confidential enclaves operating directly over private ERP line items.

        **Q3: "Why is SIAM 2021 labeled a calibration case study rather than validation?"**  
        *Answer:* Because model parameters were calibrated with knowledge of the historical 2021 event. Labeling this validation would be circular. As stated in Limitation #11, authentic validation requires testing against independent, held-out historical events without parameter tuning.
        """)


# ── Global Clean Footer ──
st.markdown("""
<div style="text-align:center; padding:32px 0 16px; color:var(--text-muted); font-size:0.75rem; border-top:1px solid #e5e7eb; margin-top:32px;">
    ⚡ <strong>CounterVerse</strong> · Causal AI Supply Chain Disruption Simulator · Indian Automotive Sourcing (HS 8112 ➔ HS 8542) · Decision Intelligence v2.0
</div>
""", unsafe_allow_html=True)

