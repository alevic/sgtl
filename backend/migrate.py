import os
import pathlib

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

BASELINE_REVISION = "2024111801"
BASE_DIR = pathlib.Path(__file__).parent


def get_alembic_config() -> Config:
    cfg = Config(str(BASE_DIR / "alembic.ini"))
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        cfg.set_main_option("sqlalchemy.url", database_url)
    return cfg


def ensure_baseline(cfg: Config) -> None:
    url = cfg.get_main_option("sqlalchemy.url")
    engine = create_engine(url)
    insp = inspect(engine)
    table_names = insp.get_table_names()
    if "alembic_version" not in table_names and "links" in table_names:
        command.stamp(cfg, BASELINE_REVISION)


def run_migrations() -> None:
    cfg = get_alembic_config()
    ensure_baseline(cfg)
    command.upgrade(cfg, "head")


if __name__ == "__main__":
    run_migrations()
