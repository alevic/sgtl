#!/usr/bin/env python3
import subprocess
import sys

MODELS_FILE = "backend/models.py"
MIGRATIONS_DIR = "backend/alembic/versions/"


def get_staged_files() -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        stdout=subprocess.PIPE,
        text=True,
        check=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def main() -> int:
    staged = get_staged_files()
    if MODELS_FILE not in staged:
        return 0
    if any(path.startswith(MIGRATIONS_DIR) for path in staged):
        return 0

    sys.stderr.write(
        "backend/models.py foi modificado, mas nenhuma migration foi encontrada.\n"
        "Execute `docker compose --env-file .env -f docker-compose.dev.yml run --rm backend "
        "alembic revision --autogenerate -m \"mensagem\"` antes do commit.\n"
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
