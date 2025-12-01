# SGTL

SGTL é um mini-Linktree construído com FastAPI + PostgreSQL + React/Vite. O projeto foi evoluído via Codex com autenticação JWT, ordenação drag-and-drop, webhook com n8n e migrações automatizadas via Alembic.

## Visão Geral

- **Backend**: FastAPI, SQLAlchemy, Pydantic, Alembic.
- **Banco**: PostgreSQL (migrations automáticas).
- **Frontend**: React + TypeScript + Vite + Tailwind.
- **Infra**: Docker/Docker Compose (dev/prod), Coolify.
- **Extras**: Webhook para n8n (create/update/delete), seletor de ícones com grade, arrastar para ordenar.

## Estrutura

```
.
├── backend/
│   ├── main.py, models.py, database.py
│   ├── migrate.py (executa Alembic no startup)
│   └── alembic/
│       ├── env.py
│       └── versions/ (migrações: 2024111801/1802/1803…)
├── frontend/
│   ├── package.json
│   └── src/App.tsx (UI principal)
├── docker-compose.dev.yml
├── docker-compose.prod.yml
├── Makefile (atalhos dev)
├── .env / .env.example
└── scripts/check_migrations.py (hook para lembrar de criar migração)
```

## Funcionalidades

- CRUD de links com campos: `titulo`, `url`, `descricao`, `ordem`, `icone`.
- Autenticação JWT com `ADMIN_USERNAME` / `ADMIN_PASSWORD`.
- Painel com drag-and-drop e formulário (novo campo “Descrição” + “Ícone” com grade de seleção).
- Página pública read-only.
- Webhook n8n (`N8N_WEBHOOK_URL`) disparado em create/update/delete.
- Migrações automáticas no startup (`python migrate.py && uvicorn ...`).
- Script de verificação de migrações (pre-commit).

## Variáveis de Ambiente

`./.env.example` contempla:

```
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
SECRET_KEY=...
ACCESS_TOKEN_EXPIRE_MINUTES=120
N8N_WEBHOOK_URL=
DATABASE_URL=postgresql+psycopg2://user:password@db:5432/sgtl_db
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=sgtl_db
VITE_API_URL=http://127.0.0.1:8000
```

Use o prefixo `postgresql+psycopg2://` em produção para Alembic funcionar.

## Migrações

1. `2024111801_create_links_table`
2. `2024111802_add_descricao_to_links`
3. `2024111803_add_icone_to_links`

No startup o `migrate.py`:
- carrega `alembic.ini` com `DATABASE_URL`;
- marca baseline se necessário (`alembic stamp 2024111801`);
- roda `alembic upgrade head`.

Para rodar manualmente: `docker compose --env-file .env -f docker-compose.dev.yml run --rm backend python migrate.py`.

## Comandos Úteis (Makefile)

- `make dev-up` – sobe backend+frontend com build.
- `make dev-down`
- `make dev-logs`
- `make dev-migrate`
- `make dev-restart`

Instale o `make` no WSL via `sudo apt install make`.

## Docker remoto (build/exec na máquina Linux)

- O Makefile já define `DOCKER_HOST=tcp://192.168.0.113:2375`, então `make dev-up`/`dev-migrate` rodam contra o daemon remoto.
- Para trocar o host, use `make dev-up DOCKER_HOST=tcp://seu-host:2375` ou exporte `DOCKER_HOST` antes.
- Se o `docker` nativo não estiver instalado no WSL, o Makefile usa `docker.exe` automaticamente; mantenha o Docker Desktop com acesso à rede habilitado.
- Teste a conexão com `docker.exe -H tcp://192.168.0.113:2375 ps` (deve listar os containers remotos).
- Porta 2375 é sem TLS; mantenha a máquina na mesma rede confiável ou configure TLS/SSH se expor para fora.
- Para evitar bind mounts inválidos no host remoto, use `make dev-up-remote` (combina `docker-compose.dev.yml` + `docker-compose.remote.yml`, sem volumes locais).
- Para validar o bundle do frontend em modo produção no host remoto: `make frontend-preview-remote` (faz `npm run build` e sobe `npm run preview` expondo a porta 5173).
- No Windows/WSL sem Docker Desktop: foi instalado o cliente Docker em `~/.local/bin/docker` + plugin Compose em `~/.docker/cli-plugins/docker-compose`. O Makefile prioriza esse binário com `DOCKER_HOST=tcp://192.168.0.113:2375`, então basta usar `make dev-up-remote`/`dev-down`/etc. sem precisar do Docker Desktop local.

## Webhook n8n

Configure `N8N_WEBHOOK_URL`. Payload enviado:

```json
{
  "event": "created|updated|deleted",
  "id": 1,
  "titulo": "Meu site",
  "url": "https://...",
  "ordem": 1,
  "descricao": "...",
  "icone": "🔗"
}
```

## Fluxo de Deploy

1. Commitar mudanças (hook alerta sobre migrações faltantes).
2. Push para o branch monitorado (ex.: `main` no Coolify).
3. Redeploy backend/frontend.
   - Backend executa `python migrate.py` (garante schema).
   - Frontend é rebuildado via Vite.

Ambiente de produção usa `docker-compose.prod.yml` (backend exposto internamente, frontend via nginx, Postgres com volume dedicado).

## Próximos Passos Sugestivos

- Seeds automáticos pós-migração.
- CI que roda `alembic upgrade head` antes do deploy.
- Multiusuários, analytics de cliques, temas customizáveis.

---

Este README reflete o estado atual do projeto conforme desenvolvido e validado via Codex. Qualquer nova alteração deve manter as migrações em dia e seguir o fluxo definido acima.
