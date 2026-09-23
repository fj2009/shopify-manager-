.PHONY: build up down logs reset backend migrate seed prod followup check

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

reset:
	docker compose down -v

backend:
	docker compose exec backend bash

migrate:
	docker compose exec backend alembic upgrade head

seed:
	docker compose exec backend python -m app.core.seed

prod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

followup:
	docker compose exec backend python -m app.worker.followup

check:
	python3 -m compileall -q backend/app backend/alembic
	@echo "OK"