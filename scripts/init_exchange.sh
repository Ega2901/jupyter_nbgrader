#!/usr/bin/env bash
set -euo pipefail

VOL="nb-exchange"
IMG="${DOCKER_JUPYTER_IMAGE:-nbgrader-singleuser:latest}"

docker volume create "$VOL" >/dev/null

# выставляем права 1777 внутри volume от root
docker run --rm -u 0 -v "$VOL":/srv/nbgrader/exchange "$IMG" \
  bash -lc "mkdir -p /srv/nbgrader/exchange && chmod 1777 /srv/nbgrader/exchange"

echo "[ok] exchange готов (nb-exchange, chmod 1777)."
