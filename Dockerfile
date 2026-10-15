# ── Stage 1: builder ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# System deps — removed libpq-dev (PostgreSQL), added default-libmysqlclient-dev for MySQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Use Tsinghua mirror as fallback in case PyPI is slow/blocked
RUN pip install --upgrade pip \
 && pip install --prefix=/install --no-cache-dir \
    -i https://pypi.org/simple \
    --extra-index-url https://mirrors.aliyun.com/pypi/simple \
    -r requirements.txt


# ── Stage 2: runtime ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

LABEL org.opencontainers.image.title="AI Customer Support Agent Platform" \
      org.opencontainers.image.description="FastAPI + LangGraph multi-agent support system" \
      org.opencontainers.image.source="https://github.com/your-org/ai-support-platform"

# Runtime MySQL client lib
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root user for security
RUN groupadd --gid 1001 appgroup \
 && useradd  --uid 1001 --gid appgroup --shell /bin/sh --create-home appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY app/       ./app/
COPY frontend/  ./frontend/
COPY scripts/   ./scripts/
COPY tests/     ./tests/

# Pre-download the embedding model so it is baked into the image
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# Sentence-transformers caches under ~/.cache — make it accessible
ENV TRANSFORMERS_CACHE=/app/.cache
RUN mkdir -p /app/.cache && chown -R appuser:appgroup /app

USER appuser

# Expose FastAPI port
EXPOSE 8000
EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Production: multiple Uvicorn workers behind the ASGI server
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "2", \
     "--log-level", "info", \
     "--access-log"]
