# ── Stage 1: Builder ──────────────────────────────────────────────────────────
FROM python:3.10-slim AS builder

WORKDIR /build

# System dependencies for psycopg2, bcrypt, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies into a local prefix for copying
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --prefix=/install --no-cache-dir -r requirements.txt


# ── Stage 2: Runtime ──────────────────────────────────────────────────────────
FROM python:3.10-slim AS runtime

LABEL maintainer="VendorOS Team"
LABEL description="VendorOS Street Food Vendor Management Platform"
LABEL version="1.0.0"

# Non-root user for security
RUN groupadd -r vendoros && useradd -r -g vendoros -d /app -s /sbin/nologin vendoros

WORKDIR /app

# Runtime system dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY --chown=vendoros:vendoros . .

# Drop to non-root
USER vendoros

# Expose port
EXPOSE 8000

# Health check for container orchestrator
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run Alembic migrations then start Uvicorn
CMD ["sh", "-c", \
     "alembic upgrade head && \
      uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --workers 2 \
        --loop uvloop \
        --http httptools \
        --access-log \
        --log-level info"]