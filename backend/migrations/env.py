from logging.config import fileConfig
from alembic import context
from backend.app.db import engine, Base
from backend.app import models  # noqa: F401

if context.config.config_file_name:
    fileConfig(context.config.config_file_name)

if context.is_offline_mode():
    context.configure(
        url=str(engine.url),
        target_metadata=Base.metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    with engine.connect() as connection:
        context.configure(
            connection=connection, target_metadata=Base.metadata, compare_type=True
        )
        with context.begin_transaction():
            context.run_migrations()
