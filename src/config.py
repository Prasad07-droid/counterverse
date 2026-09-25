# -*- coding: utf-8 -*-
"""
Centralized Configuration Management for CounterVerse
=====================================================
Uses pydantic-settings for validated, type-safe configuration with
environment variable overrides and .env file support.

Priority order (highest → lowest):
  1. Environment variables (prefixed COUNTERVERSE_)
  2. .env file in project root
  3. Defaults defined below
"""

import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ── Project Root Detection ──
# Works whether called from src/, app/, api/, tests/, or project root
_THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = _THIS_FILE.parent.parent  # src/config.py → project root

# ── Try pydantic-settings, fall back to manual env parsing ──
try:
    from pydantic_settings import BaseSettings
    from pydantic import Field, field_validator
    _HAS_PYDANTIC_SETTINGS = True
except ImportError:
    _HAS_PYDANTIC_SETTINGS = False


if _HAS_PYDANTIC_SETTINGS:
    class _Settings(BaseSettings):
        """Validated application settings. Override via env vars or .env file."""

        # ── Paths ──
        data_dir: Path = Field(default_factory=lambda: PROJECT_ROOT / "data")
        raw_data_dir: Path = Field(default_factory=lambda: PROJECT_ROOT / "data" / "raw")
        processed_data_dir: Path = Field(default_factory=lambda: PROJECT_ROOT / "data" / "processed")
        cache_db_path: Path = Field(
            default_factory=lambda: PROJECT_ROOT / "data" / "processed" / "headline_cache.db",
            description="SQLite headline cache database path"
        )
        graph_persistence_path: Path = Field(
            default_factory=lambda: PROJECT_ROOT / "data" / "processed" / "grounding_graph_custom.json",
            description="Disk-backed graph overlay persistence path"
        )
        comtrade_baseline_path: Path = Field(
            default_factory=lambda: PROJECT_ROOT / "data" / "processed" / "comtrade_india_baseline.json"
        )

        # ── API Keys (optional) ──
        comtrade_api_key: Optional[str] = Field(default=None, description="UN Comtrade API key")
        huggingface_token: Optional[str] = Field(default=None, description="HuggingFace access token")

        # ── Financial Constants ──
        usd_inr_rate: float = Field(default=83.0, description="USD/INR exchange rate")
        hs8542_baseline_crore: float = Field(
            default=133814.34,
            description="India HS 8542 imports baseline in Crore INR (2022 Full Year)"
        )
        hs8112_baseline_crore: float = Field(
            default=552.84,
            description="India HS 8112 imports baseline in Crore INR (2022 Full Year)"
        )
        comtrade_data_vintage: str = Field(
            default="2022",
            description="Active Comtrade data vintage year (2022_audited | 2023_preliminary | custom)"
        )

        # ── Monte Carlo Defaults ──
        mc_n_samples: int = Field(default=10000, ge=100, le=1000000)
        mc_random_seed: int = Field(default=42)
        spot_premium_low: float = Field(default=1.3, ge=1.0)
        spot_premium_high: float = Field(default=2.8, le=5.0)

        # ── GDELT / News Ingestion ──
        gdelt_max_records: int = Field(default=8, ge=1, le=250)
        gdelt_max_retries: int = Field(default=3, ge=1, le=10)
        gdelt_timeout_seconds: float = Field(default=6.0, ge=1.0)
        news_cache_max_age_hours: int = Field(default=24, ge=1)
        rss_enabled: bool = Field(default=True, description="Enable Google/Bing News RSS fallback")

        # ── SLM Configuration ──
        slm_model_name: str = Field(default="Qwen/Qwen2.5-0.5B-Instruct")
        slm_precision: str = Field(default="bfloat16")
        slm_max_new_tokens: int = Field(default=512, ge=64, le=2048)
        slm_load_timeout_seconds: int = Field(default=45, ge=10)

        # ── Risk Engine Thresholds ──
        risk_threshold_high: float = Field(default=0.60, ge=0.0, le=1.0)
        risk_threshold_medium: float = Field(default=0.45, ge=0.0, le=1.0)

        # ── API Server ──
        api_host: str = Field(default="0.0.0.0")
        api_port: int = Field(default=8000, ge=1024, le=65535)
        api_workers: int = Field(default=1, ge=1, le=16)

        # ── Dashboard ──
        streamlit_port: int = Field(default=8501, ge=1024, le=65535)

        model_config = {
            "env_prefix": "COUNTERVERSE_",
            "env_file": str(PROJECT_ROOT / ".env"),
            "env_file_encoding": "utf-8",
            "extra": "ignore",
        }

    def _load_settings() -> _Settings:
        try:
            return _Settings()
        except Exception as e:
            logger.warning(f"Failed to load pydantic settings: {e}. Using defaults.")
            return _Settings.model_construct()

    settings = _load_settings()

else:
    # ── Fallback: Simple dataclass-like config without pydantic ──
    class _FallbackSettings:
        """Minimal settings fallback when pydantic-settings is not installed."""

        def __init__(self):
            self.data_dir = PROJECT_ROOT / "data"
            self.raw_data_dir = PROJECT_ROOT / "data" / "raw"
            self.processed_data_dir = PROJECT_ROOT / "data" / "processed"
            self.cache_db_path = PROJECT_ROOT / "data" / "processed" / "headline_cache.db"
            self.graph_persistence_path = PROJECT_ROOT / "data" / "processed" / "grounding_graph_custom.json"
            self.comtrade_baseline_path = PROJECT_ROOT / "data" / "processed" / "comtrade_india_baseline.json"

            self.comtrade_api_key = os.environ.get("COUNTERVERSE_COMTRADE_API_KEY")
            self.huggingface_token = os.environ.get("COUNTERVERSE_HUGGINGFACE_TOKEN")

            self.usd_inr_rate = float(os.environ.get("COUNTERVERSE_USD_INR_RATE", "83.0"))
            self.hs8542_baseline_crore = float(os.environ.get("COUNTERVERSE_HS8542_BASELINE_CRORE", "133814.34"))
            self.hs8112_baseline_crore = float(os.environ.get("COUNTERVERSE_HS8112_BASELINE_CRORE", "552.84"))
            self.comtrade_data_vintage = os.environ.get("COUNTERVERSE_COMTRADE_DATA_VINTAGE", "2022")

            self.mc_n_samples = int(os.environ.get("COUNTERVERSE_MC_N_SAMPLES", "10000"))
            self.mc_random_seed = int(os.environ.get("COUNTERVERSE_MC_RANDOM_SEED", "42"))
            self.spot_premium_low = float(os.environ.get("COUNTERVERSE_SPOT_PREMIUM_LOW", "1.3"))
            self.spot_premium_high = float(os.environ.get("COUNTERVERSE_SPOT_PREMIUM_HIGH", "2.8"))

            self.gdelt_max_records = int(os.environ.get("COUNTERVERSE_GDELT_MAX_RECORDS", "8"))
            self.gdelt_max_retries = int(os.environ.get("COUNTERVERSE_GDELT_MAX_RETRIES", "3"))
            self.gdelt_timeout_seconds = float(os.environ.get("COUNTERVERSE_GDELT_TIMEOUT_SECONDS", "6.0"))
            self.news_cache_max_age_hours = int(os.environ.get("COUNTERVERSE_NEWS_CACHE_MAX_AGE_HOURS", "24"))
            self.rss_enabled = os.environ.get("COUNTERVERSE_RSS_ENABLED", "true").lower() == "true"

            self.slm_model_name = os.environ.get("COUNTERVERSE_SLM_MODEL_NAME", "Qwen/Qwen2.5-0.5B-Instruct")
            self.slm_precision = os.environ.get("COUNTERVERSE_SLM_PRECISION", "bfloat16")
            self.slm_max_new_tokens = int(os.environ.get("COUNTERVERSE_SLM_MAX_NEW_TOKENS", "512"))
            self.slm_load_timeout_seconds = int(os.environ.get("COUNTERVERSE_SLM_LOAD_TIMEOUT_SECONDS", "45"))

            self.risk_threshold_high = float(os.environ.get("COUNTERVERSE_RISK_THRESHOLD_HIGH", "0.60"))
            self.risk_threshold_medium = float(os.environ.get("COUNTERVERSE_RISK_THRESHOLD_MEDIUM", "0.45"))

            self.api_host = os.environ.get("COUNTERVERSE_API_HOST", "0.0.0.0")
            self.api_port = int(os.environ.get("COUNTERVERSE_API_PORT", "8000"))
            self.api_workers = int(os.environ.get("COUNTERVERSE_API_WORKERS", "1"))

            self.streamlit_port = int(os.environ.get("COUNTERVERSE_STREAMLIT_PORT", "8501"))

    settings = _FallbackSettings()
    logger.info("Using fallback settings (install pydantic-settings for validation).")
