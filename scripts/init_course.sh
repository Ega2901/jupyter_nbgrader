#!/usr/bin/env bash
set -euo pipefail

IMG="${DOCKER_JUPYTER_IMAGE:-nbgrader-singleuser:latest}"
USER_NAME="${JUPYTERHUB_ADMIN:-instructor}"
COURSE_VOL="courses-${USER_NAME}"
COURSE_DIR_IN_VOL="/home/jovyan/mycourse"

docker volume create "${COURSE_VOL}" >/dev/null

# копируем seed-курс в volume через временный контейнер
TMP_CID=$(docker create -v "${COURSE_VOL}":/home/jovyan "${IMG}" true)
docker cp courses_seed/mycourse "${TMP_CID}:${COURSE_DIR_IN_VOL}"
docker start "${TMP_CID}" >/dev/null
docker rm "${TMP_CID}" >/dev/null

# права владельца (1000:100 = jovyan)
docker run --rm -u 0 -v "${COURSE_VOL}":/home/jovyan "${IMG}" bash -lc "
  chown -R 1000:100 ${COURSE_DIR_IN_VOL} &&
  find ${COURSE_DIR_IN_VOL} -type d -exec chmod 755 {} \; &&
  find ${COURSE_DIR_IN_VOL} -type f -exec chmod 644 {} \;
"

echo "[ok] mycourse скопирован в volume ${COURSE_VOL}:${COURSE_DIR_IN_VOL}"
