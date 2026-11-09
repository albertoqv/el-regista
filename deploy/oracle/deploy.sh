#!/usr/bin/env bash
# Pull main and rebuild on the VM. From the PC:
#   ssh ubuntu@<ip> '~/el-regista/deploy/oracle/deploy.sh'
set -euo pipefail
cd "$(dirname "$0")"
git -C ../.. pull --ff-only

profiles=()
grep -q '@db:5432' .env && profiles=(--profile localdb)

# API and Caddy first: the web's build may read the API through its public name.
docker compose "${profiles[@]}" up -d --build --remove-orphans api caddy
for _ in $(seq 60); do
  docker compose exec -T api python -c \
    "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4)" \
    2>/dev/null && break
  sleep 5
done
docker compose "${profiles[@]}" up -d --build --remove-orphans
docker image prune -f >/dev/null
docker compose ps
