# -*- coding: utf-8 -*-
"""
Additional configuration extensions for CounterVerse.
These values are loaded via the main config (src/config.py) fallback class.
"""
import os

# Neo4j connection settings (optional – used when Neo4j service is enabled)
NEO4J_URI = os.getenv("COUNTERVERSE_NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("COUNTERVERSE_NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("COUNTERVERSE_NEO4J_PASSWORD", "password")

# ESG and additional risk factor weights (must sum to 1.0)
RISK_WEIGHTS = {
    "business": 0.30,
    "financial": 0.25,
    "operational": 0.20,
    "esg": 0.15,
    "geopolitical": 0.10,
}

# Languages supported for news ingestion (ISO‑639‑1 codes)
SUPPORTED_LANGUAGES = ["en", "hi", "ta"]

# UI / visual flags
UI_DARK_MODE = os.getenv("COUNTERVERSE_UI_DARK_MODE", "true").lower() == "true"
UI_GLASSMORPHISM = os.getenv("COUNTERVERSE_UI_GLASSMORPHISM", "true").lower() == "true"
