# Render free web service: API and web in one container (512 MB, sleeps after 15 min
# without visits). Bridge while Vercel Hobby keeps the account paused and the Oracle VM
# has no capacity. Built from the repository root (render.yaml).
# Render hands every environment variable to the build as an argument: with
# DATABASE_URL the API runs during `next build`, so the home page and rankings are
# prerendered with data. It only exists in this stage, never in the final image.
FROM python:3.14-slim AS build
RUN apt-get update && apt-get install -y --no-install-recommends libstdc++6 \
    && rm -rf /var/lib/apt/lists/* && pip install --no-cache-dir uv
COPY --from=node:24-slim /usr/local/bin/node /usr/local/bin/node
COPY --from=node:24-slim /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY alembic.ini ./
COPY alembic ./alembic
COPY src ./src
RUN uv sync --frozen --no-dev

WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
# RENDER_EXTERNAL_URL: the service's own address (https://<name>.onrender.com).
ARG RENDER_EXTERNAL_URL=http://localhost:10000
ARG DATABASE_URL=""
ENV NEXT_PUBLIC_API_URL=${RENDER_EXTERNAL_URL}/api \
    NEXT_PUBLIC_SITE_URL=${RENDER_EXTERNAL_URL} \
    API_INTERNAL_URL=http://127.0.0.1:8000 NEXT_TELEMETRY_DISABLED=1
RUN if [ -n "$DATABASE_URL" ]; then \
      (cd /app && RATE_LIMIT_PER_MINUTE=100000 /app/.venv/bin/uvicorn \
        player_scouting.presentation.api.main:app --host 127.0.0.1 --port 8000 \
        >/tmp/api.log 2>&1 &) ; \
      for _ in $(seq 60); do \
        node -e "fetch('http://127.0.0.1:8000/health').then(r=>process.exit(r.ok?0:1),()=>process.exit(1))" && break; \
        sleep 2; \
      done; \
    fi; \
    npm run build

FROM python:3.14-slim
RUN apt-get update \
    && apt-get upgrade -y --no-install-recommends \
    && apt-get install -y --no-install-recommends libstdc++6 \
    && rm -rf /var/lib/apt/lists/* \
    && python -m pip uninstall -y pip setuptools wheel \
    && useradd --system --uid 10001 --create-home --shell /usr/sbin/nologin app
COPY --from=build /usr/local/bin/node /usr/local/bin/node
COPY --from=build /app /app
COPY --from=build --chown=app /web/.next/standalone /web
COPY --from=build --chown=app /web/.next/static /web/.next/static
COPY --from=build --chown=app /web/public /web/public
COPY deploy/render/start.sh /start.sh
# Every server-side request of the web reaches the API from 127.0.0.1: the
# per-address limit must leave room for them. Next's heap is capped so both fit.
# REQUIRE_INGESTION_KEY is an on/off switch, not a secret (Trivy DS-0031 matches "KEY").
# trivy:ignore:DS-0031
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1 MALLOC_ARENA_MAX=2 \
    NODE_ENV=production NODE_OPTIONS=--max-old-space-size=192 \
    API_INTERNAL_URL=http://127.0.0.1:8000 \
    REQUIRE_INGESTION_KEY=true EXPOSE_DOCS=false RATE_LIMIT_PER_MINUTE=6000
USER app
EXPOSE 10000
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD ["node", "-e", "fetch('http://127.0.0.1:'+(process.env.PORT||10000)+'/robots.txt').then(r => process.exit(r.ok ? 0 : 1), () => process.exit(1))"]
CMD ["sh", "/start.sh"]
