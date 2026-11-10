# Hugging Face Space (free CPU tier, Docker): API + web + Caddy in one container on
# port 7860. Bridge while the Oracle VM has no capacity. Built from GitHub's main.
# Space variable SITE_URL (https://<user>-<space>.hf.space) arrives as a build arg;
# the secret DATABASE_URL is mounted during the build (the API runs while Next
# prerenders the home page and rankings) and both secrets are read at run time.
FROM python:3.14-slim AS build
RUN apt-get update && apt-get install -y --no-install-recommends git libstdc++6 \
    && rm -rf /var/lib/apt/lists/* && pip install --no-cache-dir uv
COPY --from=node:24-slim /usr/local/bin/node /usr/local/bin/node
COPY --from=node:24-slim /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm

ARG REPO=https://github.com/albertoqv/el-regista.git
ARG REF=main
# Any new value (Space variable CACHE_BUST) forces a fresh clone of main.
ARG CACHE_BUST=0
RUN git clone --depth 1 --branch "$REF" "$REPO" /src
WORKDIR /app
RUN cp /src/pyproject.toml /src/uv.lock /src/alembic.ini ./ \
    && cp -r /src/alembic /src/src ./ && uv sync --frozen --no-dev

WORKDIR /web
RUN cp -r /src/web/. . && npm ci
ARG SITE_URL=http://localhost:7860
ENV NEXT_PUBLIC_API_URL=${SITE_URL}/_api NEXT_PUBLIC_SITE_URL=${SITE_URL} \
    API_INTERNAL_URL=http://127.0.0.1:8000 NEXT_TELEMETRY_DISABLED=1
RUN --mount=type=secret,id=DATABASE_URL,mode=0444,required=false \
    if [ -s /run/secrets/DATABASE_URL ]; then \
      (cd /app && DATABASE_URL="$(cat /run/secrets/DATABASE_URL)" \
        /app/.venv/bin/uvicorn player_scouting.presentation.api.main:app \
        --host 127.0.0.1 --port 8000 >/tmp/api.log 2>&1 &) ; \
      for _ in $(seq 60); do \
        node -e "fetch('http://127.0.0.1:8000/health').then(r=>process.exit(r.ok?0:1),()=>process.exit(1))" && break; \
        sleep 2; \
      done; \
    fi; \
    npm run build

FROM python:3.14-slim
RUN apt-get update && apt-get install -y --no-install-recommends libstdc++6 ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --uid 1000 --create-home user
COPY --from=caddy:2.10-alpine /usr/bin/caddy /usr/local/bin/caddy
COPY --from=build /usr/local/bin/node /usr/local/bin/node
COPY --from=build --chown=user /app /app
COPY --from=build --chown=user /web/.next/standalone /web
COPY --from=build --chown=user /web/.next/static /web/.next/static
COPY --from=build --chown=user /web/public /web/public
COPY --chown=user Caddyfile start.sh /srv/
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1 MALLOC_ARENA_MAX=2 \
    NODE_ENV=production API_INTERNAL_URL=http://127.0.0.1:8000 \
    REQUIRE_INGESTION_KEY=true EXPOSE_DOCS=false RATE_LIMIT_PER_MINUTE=6000 \
    XDG_DATA_HOME=/tmp XDG_CONFIG_HOME=/tmp
USER user
EXPOSE 7860
CMD ["bash", "/srv/start.sh"]
