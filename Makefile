.PHONY: build up down logs init-exchange init-course instructor-login collect autograde formgrade feedback export plag

DOCKER_JUPYTER_IMAGE ?= nbgrader-singleuser:latest

build:
	# собрать single-user образ
	docker build -t $(DOCKER_JUPYTER_IMAGE) -f Dockerfile.singleuser .
	# собрать hub образ
	docker build -t nbgrader-hub:latest -f Dockerfile.hub .

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

init-exchange:
	bash scripts/init_exchange.sh

init-course:
	bash scripts/init_course.sh

instructor-login:
	@echo "Открой: http://localhost:$${HUB_PORT:-8000}"
	@echo "Логин: $${JUPYTERHUB_ADMIN:-instructor}   Пароль: $${DUMMY_SHARED_PASSWORD:-letmein}"

# ====== grading pipeline (подсказки) ======
ASSIGN?=assignment1
collect:
	@echo "В терминале инструктора (~/mycourse): nbgrader collect $(ASSIGN)"

autograde:
	@echo "В терминале инструктора (~/mycourse): nbgrader autograde $(ASSIGN)"

formgrade:
	@echo "В терминале инструктора (~/mycourse): nbgrader formgrade"

feedback:
	@echo "В терминале инструктора (~/mycourse): nbgrader feedback $(ASSIGN)"

export:
	@echo "В терминале инструктора (~/mycourse): nbgrader export --to csv --filename grades_$(ASSIGN).csv"

plag:
	@echo "В терминале инструктора (~/mycourse): python scripts/antiplag.py --assignment $(ASSIGN) --root submitted --out reports/plag_$(ASSIGN)"
