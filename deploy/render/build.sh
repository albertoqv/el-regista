#!/bin/sh
# Builds the web with the API running, so the home page and rankings are prerendered
# with data. A script and not an inline RUN: Render prints each RUN line with the build
# arguments filled in, and DATABASE_URL (password included) ended up in its logs.
set -eu
if [ -n "${DATABASE_URL:-}" ]; then
  (cd /app && RATE_LIMIT_PER_MINUTE=100000 /app/.venv/bin/uvicorn \
    player_scouting.presentation.api.main:app --host 127.0.0.1 --port 8000 \
    >/tmp/api.log 2>&1 &)
  for _ in $(seq 60); do
    node -e "fetch('http://127.0.0.1:8000/health').then(r=>process.exit(r.ok?0:1),()=>process.exit(1))" \
      && break
    sleep 2
  done
  echo "API during the build:"
  tail -n 5 /tmp/api.log
else
  echo "No DATABASE_URL in the build: pages are prerendered without data"
fi
cd /web
npm run build
if [ -n "${DATABASE_URL:-}" ]; then
  echo "API errors:"
  grep -E " [45][0-9][0-9] |Error" /tmp/api.log | tail -n 10 || true
fi
