DOCKER_HOST_DEV ?= tcp://192.168.0.113:2375
DOCKER_HOST_PROD ?= tcp://a2tec.com.br:2375
DOCKER_HOST ?= $(DOCKER_HOST_DEV)
DOCKER_BIN ?= $(shell if [ -x $$HOME/.local/bin/docker ]; then echo $$HOME/.local/bin/docker; elif command -v docker >/dev/null 2>&1; then echo docker; elif command -v docker.exe >/dev/null 2>&1; then echo docker.exe; else echo docker; fi)
DOCKER_FLAGS ?= --host $(DOCKER_HOST)

DEV_COMPOSE=$(DOCKER_BIN) $(DOCKER_FLAGS) compose --env-file .env -f docker-compose.dev.yml
DEV_COMPOSE_REMOTE=$(DOCKER_BIN) $(DOCKER_FLAGS) compose --env-file .env -f docker-compose.remote.yml
PROD_COMPOSE=$(DOCKER_BIN) $(DOCKER_FLAGS) compose --env-file .env -f docker-compose.prod.yml

.PHONY: dev-up dev-up-nobuild dev-up-remote dev-down dev-down-remote dev-build-remote dev-logs dev-migrate dev-restart frontend-preview-remote prod-build

dev-up:
	$(DEV_COMPOSE) up -d --build backend frontend

dev-up-nobuild:
	$(DEV_COMPOSE) up -d backend frontend

dev-up-remote:
	$(DEV_COMPOSE_REMOTE) up -d --build backend frontend

dev-down:
	$(DEV_COMPOSE) down

dev-down-remote:
	$(DEV_COMPOSE_REMOTE) down

dev-build-remote:
	$(DEV_COMPOSE_REMOTE) build backend frontend

dev-logs:
	$(DEV_COMPOSE) logs -f backend frontend

dev-migrate:
	$(DEV_COMPOSE) run --rm backend python migrate.py

dev-restart:
	$(DEV_COMPOSE) restart backend frontend

frontend-preview-remote:
	$(DEV_COMPOSE_REMOTE) run --rm frontend sh -c "npm run build"
	$(DEV_COMPOSE_REMOTE) run --rm --service-ports frontend npm run preview -- --host 0.0.0.0 --port 5173

prod-build:
	$(PROD_COMPOSE) build
