#!/usr/bin/env bash
# One container, three processes: if any of them dies, exit so the Space restarts.
set -euo pipefail
cd /app
alembic upgrade head
uvicorn player_scouting.presentation.api.main:app --host 127.0.0.1 --port 8000 &
(cd /web && HOSTNAME=127.0.0.1 PORT=3000 exec node server.js) &
caddy run --config /srv/Caddyfile --adapter caddyfile &
wait -n
exit 1
