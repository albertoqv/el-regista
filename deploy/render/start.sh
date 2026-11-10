#!/bin/sh
# One container, two processes: the API on 127.0.0.1:8000 (only the web reaches it)
# and the web on Render's $PORT. If either dies, exit so Render restarts the service.
# Migrations are not run here: the data refresh applies them.
set -eu
cd /app
uvicorn player_scouting.presentation.api.main:app --host 127.0.0.1 --port 8000 &
api=$!
cd /web
HOSTNAME=0.0.0.0 PORT="${PORT:-10000}" node server.js &
web=$!
while kill -0 "$api" 2>/dev/null && kill -0 "$web" 2>/dev/null; do
  sleep 5
done
exit 1
