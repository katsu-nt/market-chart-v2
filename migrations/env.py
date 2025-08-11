import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool, MetaData

# ensure app package is importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# load .env
try:
    from dotenv import load_dotenv, find_dotenv
    load_dotenv(find_dotenv())
except Exception:
    pass

# Alembic Config object
config = context.config

# --- Lấy DATABASE_URL từ env ---
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "Missing DATABASE_URL. Please set it in your environment or .env file.\n"
        "Example: postgresql+psycopg2://user:password@127.0.0.1:5432/market_db?sslmode=disable"
    )

# Inject URL vào alembic config
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Logging config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- Import models' metadata ---
from app.models.gold import Base as GoldBase
from app.models.exchange import Base as ExchangeBase

# Merge metadata từ nhiều Base
metadata = MetaData()
for m in (GoldBase.metadata, ExchangeBase.metadata):
    for t in m.tables.values():
        if t.name not in metadata.tables:
            t.tometadata(metadata)

target_metadata = metadata

# Debug: In URL (mask password)
try:
    from sqlalchemy.engine.url import make_url
    url_obj = make_url(DATABASE_URL)
    safe_url = url_obj._replace(password="***")
    print("Alembic URL ->", safe_url)
except Exception:
    pass


def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section) or {},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
