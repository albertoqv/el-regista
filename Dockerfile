FROM python:3.14-slim

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY alembic.ini ./
COPY alembic ./alembic
COPY src ./src
# Install the project itself now that its code is here (uvicorn runs without uv).
RUN uv sync --frozen --no-dev

# Fewer glibc malloc arenas: less resident memory for a single process, and
# memory is almost all of the Railway bill.
ENV PATH="/app/.venv/bin:$PATH" MALLOC_ARENA_MAX=2 PYTHONUNBUFFERED=1 \
    REQUIRE_INGESTION_KEY=true EXPOSE_DOCS=false

EXPOSE 8000

# exec: uvicorn replaces the shell, no extra uv/sh processes stay resident.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn player_scouting.presentation.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
