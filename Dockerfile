# Builder: uv resolves the locked dependencies into /app/.venv.
FROM python:3.14-slim AS builder

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY alembic.ini ./
COPY alembic ./alembic
COPY src ./src
# Install the project itself now that its code is here (uvicorn runs without uv).
RUN uv sync --frozen --no-dev

# Runtime: only the virtualenv and the code, on a patched base, without pip and
# without root (Trivy DS-0002 and the base image's fixable HIGH/CRITICAL CVEs).
FROM python:3.14-slim

RUN apt-get update \
    && apt-get upgrade -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/* \
    && python -m pip uninstall -y pip setuptools wheel \
    && useradd --system --uid 10001 --no-create-home --shell /usr/sbin/nologin app

WORKDIR /app
COPY --from=builder /app /app

# Fewer glibc malloc arenas: less resident memory for a single process.
# REQUIRE_INGESTION_KEY is an on/off switch, not a secret: Trivy's DS-0031 matches
# the word "KEY" in its name.
# trivy:ignore:DS-0031
ENV PATH="/app/.venv/bin:$PATH" MALLOC_ARENA_MAX=2 PYTHONUNBUFFERED=1 \
    REQUIRE_INGESTION_KEY=true EXPOSE_DOCS=false

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\", \"8000\")}/health', timeout=4)"

# exec: uvicorn replaces the shell, no extra uv/sh processes stay resident.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn player_scouting.presentation.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
