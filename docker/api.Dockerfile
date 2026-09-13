# ─────────────────────────────────────────────────────────────
#  RAGLens API — Dockerfile
#  Multi-stage build: deps layer + slim runtime image.
#  Build context: repo root (so we can COPY apps/api/)
# ─────────────────────────────────────────────────────────────

# ── Stage 1: build dependencies ───────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build tools needed for native packages (bcrypt, cryptography, psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file first for better layer caching
COPY apps/api/requirements.txt ./

RUN pip install --upgrade pip --no-cache-dir \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: runtime image ─────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Runtime system deps (libpq for psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY apps/api/ ./

# Non-root user for security
RUN addgroup --system raglens && adduser --system --ingroup raglens raglens
RUN chown -R raglens:raglens /app
USER raglens

EXPOSE 8000

# Run Alembic migrations then start the server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
