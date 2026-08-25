# ==============================================================================
# OTZAR Geological Intelligence Backend - Ultra-fast UV Dockerfile for Coolify
# ==============================================================================

# Official Astral UV base image with Python 3.11 pre-configured
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS base

# UV and Python optimization flags
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Set working directory
WORKDIR /app

# Install minimal system tools (curl for healthchecks, gcc/libpq for postgres)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy only uv lock and project definitions first (Docker layer caching)
COPY pyproject.toml uv.lock ./

# Fast, deterministic dependency installation from uv.lock
RUN uv sync --frozen --no-install-project --no-dev

# Copy application source code and migrations
COPY app/ ./app/
COPY migrations/ ./migrations/
COPY alembic.ini .

# Create a non-root system user for security
RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 --ingroup appgroup --home /app appuser && \
    chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Expose API application port
EXPOSE 8000

# Container Healthcheck for Coolify
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Launch ASGI server directly inside the UV virtual environment
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--proxy-headers", "--forwarded-allow-ips", "*"]
