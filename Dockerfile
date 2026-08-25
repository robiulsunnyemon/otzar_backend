# ==============================================================================
# OTZAR Geological Intelligence Backend - Production Dockerfile for Coolify
# ==============================================================================

FROM python:3.11-slim AS base

# Set environment variables for Python in Docker
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8000

# Set working directory
WORKDIR /app

# Install minimal OS dependencies for PostgreSQL & Cryptography
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency definition first (layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code and migrations
COPY app/ ./app/
COPY migrations/ ./migrations/
COPY alembic.ini .
COPY pyproject.toml .

# Create a non-root user for enhanced security
RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 --ingroup appgroup --home /app appuser && \
    chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Expose API application port
EXPOSE 8000

# Docker Healthcheck (Used by Coolify to verify container status)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Launch production ASGI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--proxy-headers", "--forwarded-allow-ips", "*"]
