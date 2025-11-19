DEV_COMPOSE=docker compose --env-file .env -f docker-compose.dev.yml

.PHONY: dev-up dev-down dev-logs dev-migrate dev-restart

dev-up:
	$(DEV_COMPOSE) up -d --build backend frontend

dev-down:
	$(DEV_COMPOSE) down

dev-logs:
	$(DEV_COMPOSE) logs -f backend frontend

dev-migrate:
	$(DEV_COMPOSE) run --rm backend python migrate.py

dev-restart:
	$(DEV_COMPOSE) restart backend frontend
