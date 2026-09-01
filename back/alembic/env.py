"""Alembic 마이그레이션 환경.

- 접속 URL은 alembic.ini가 아니라 앱과 동일하게 back/.env의 DATABASE_URL을 씁니다
  (app/core/config.py). 따라서 alembic.ini에는 sqlalchemy.url을 두지 않습니다.
- target_metadata는 app/db/models.py의 Base.metadata라서
  `alembic revision --autogenerate`가 모델 변경을 감지합니다.
"""
import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# back/ 를 import 경로에 추가 (alembic을 어디서 실행하든 `import app...`이 되도록)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings  # noqa: E402
from app.db.models import Base  # noqa: E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# .env의 DATABASE_URL을 alembic 접속 URL로 주입
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
