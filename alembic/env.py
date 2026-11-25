from logging.config import fileConfig

from sqlalchemy import engine_from_config, event, pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Import load_dotenv to load environment variables
from dotenv import load_dotenv
import os
import asyncio

# Load environment variables
load_dotenv()

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Importa todos os modelos da aplicação para registrar todas as tabelas em Base.metadata
from src.resources.database import Base
import src.models  # noqa: F401

target_metadata = Base.metadata


def _resolve_sqlalchemy_url() -> str:
    """Resolve a URL do banco SQLite priorizando override explícito e variáveis de ambiente."""
    x_args = context.get_x_argument(as_dictionary=True)
    if x_args.get("sqlalchemy.url"):
        return x_args["sqlalchemy.url"]

    raw_ini_url = ""
    if config.file_config.has_option(config.config_ini_section, "sqlalchemy.url"):
        raw_ini_url = config.file_config.get(
            config.config_ini_section, "sqlalchemy.url", raw=True
        ).strip()

    if raw_ini_url and "%(ENV_SQLITE_DSN)s" not in raw_ini_url:
        return raw_ini_url

    sqlite_dsn = (
        os.getenv("SQLITE_DSN")
        or os.getenv("APP_DB_URL")
        or "sqlite+aiosqlite:///data/app.db"
    )
    return sqlite_dsn


# Set the sqlalchemy.url in the config to the resolved SQLite DSN
resolved_url = _resolve_sqlalchemy_url()
config.set_main_option("sqlalchemy.url", resolved_url)


def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
    """Ativa a verificação de chaves estrangeiras no SQLite."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=bool(url and url.startswith("sqlite")),
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    """Executa as migrações na conexão síncrona fornecida pelo engine."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=connection.dialect.name == "sqlite",
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Executa as migrações online usando engine assíncrono (ex.: sqlite+aiosqlite)."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    if connectable.dialect.name == "sqlite":
        event.listen(connectable.sync_engine, "connect", _enable_sqlite_foreign_keys)

    try:
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)
    finally:
        await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Suporta conexão já aberta via ``config.attributes['connection']``, URLs
    assíncronas (``sqlite+aiosqlite://``) e URLs síncronas (``sqlite://``).
    """
    existing_connection = config.attributes.get("connection")
    if existing_connection is not None:
        do_run_migrations(existing_connection)
        return

    url = config.get_main_option("sqlalchemy.url") or ""
    if "+aiosqlite" in url or "+asyncpg" in url:
        asyncio.run(run_async_migrations())
        return

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    if connectable.dialect.name == "sqlite":
        event.listen(connectable, "connect", _enable_sqlite_foreign_keys)

    try:
        with connectable.connect() as connection:
            do_run_migrations(connection)
    finally:
        connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
