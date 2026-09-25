# ══════════════════════════════════════════════════════════════
# CounterVerse — Multi-Stage Production Dockerfile
# ══════════════════════════════════════════════════════════════
# Runs both the Streamlit dashboard (port 8501) and FastAPI backend (port 8000).
# GPU inference requires the nvidia/cuda base image and --gpus all at runtime.
# CPU-only mode uses the Fast Heuristic engine (no Qwen SLM).
#
# Build: docker build -t counterverse .
# Run:   docker run -p 8501:8501 -p 8000:8000 counterverse
# GPU:   docker run --gpus all -p 8501:8501 -p 8000:8000 counterverse

FROM python:3.11-slim AS base

# Prevent Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# ── System dependencies ──
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# ── Python dependencies ──
COPY requirements-local.txt .
# Install CPU-only PyTorch (lighter image; for GPU, override at runtime)
RUN pip install --no-cache-dir \
    torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements-local.txt && \
    pip install --no-cache-dir fastapi uvicorn[standard] pydantic-settings

# ── Application code ──
COPY . .

# ── Create data directories ──
RUN mkdir -p data/processed data/raw data/logs

# ── Expose ports ──
EXPOSE 8501 8000

# ── Health check ──
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# ── Entrypoint: Run both services via shell ──
# Streamlit on 8501 (background) + FastAPI on 8000 (foreground)
CMD bash -c "\
    streamlit run app/dashboard.py \
        --server.port=8501 \
        --server.address=0.0.0.0 \
        --server.headless=true \
        --browser.gatherUsageStats=false & \
    uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 1"
