# ==============================================================================
# RiskIntel — FastAPI Backend Dockerfile
# Multi-stage build:  builder (dependencies) -> runner (runtime)
# ==============================================================================

# ── Stage 1: Builder ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Install system build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ── Stage 2: Runner ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS runner

WORKDIR /app

# Copy only the installed packages from builder
COPY --from=builder /root/.local /root/.local

# Ensure local bin is in PATH
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY . .

# Create non-root user
RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 --gid 1001 appuser && \
    chown -R appuser:appgroup /app

USER appuser

# Expose the application port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/live')" || exit 1

# Run with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
