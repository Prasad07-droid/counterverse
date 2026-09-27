# ══════════════════════════════════════════════════════════════
# CounterVerse — Multi-Stage Production Dockerfile (v2)
# ══════════════════════════════════════════════════════════════
# Stage 1 (builder): install all Python dependencies
# Stage 2 (runtime): lean runtime image with no build tooling
#
# Build: docker build -t counterverse:v2 .
# Run:   docker run -p 8501:8501 -p 8000:8000 counterverse:v2
# GPU:   docker run --gpus all -p 8501:8501 -p 8000:8000 counterverse:v2

# ── Stage 1: Builder ──────────────────────────────────────────
FROM python:3.11-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Install CPU-only PyTorch (lighter image; override with CUDA at runtime)
RUN pip install --no-cache-dir \
    torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

COPY requirements-local.txt .
RUN pip install --no-cache-dir -r requirements-local.txt

# ── Stage 2: Runtime ──────────────────────────────────────────
FROM python:3.11-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source
COPY . .

# Create data directories
RUN mkdir -p data/processed data/raw data/logs

# Expose ports: Streamlit + FastAPI + Prometheus
EXPOSE 8501 8000 9090

# Health check on FastAPI
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Start Streamlit (background) + FastAPI (foreground)
CMD bash -c "\
    streamlit run app/dashboard.py \
        --server.port=8501 \
        --server.address=0.0.0.0 \
        --server.headless=true \
        --browser.gatherUsageStats=false & \
    uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 2"

