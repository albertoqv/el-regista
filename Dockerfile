FROM python:3.14-slim

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY alembic.ini ./
COPY alembic ./alembic
COPY src ./src

ENV PATH="/app/.venv/bin:$PATH"

CMD ["sh", "-c", "uv run alembic upgrade head && uv run uvicorn player_scouting.presentation.api.main:app --host 0.0.0.0 --port 8000"]
