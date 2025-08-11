import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool, MetaData
from sqlalchemy.engine.url import URL

# ensure app package is importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

# Alembic Config object
config = context.config

# ---- Build DB URL from POSTGRES_* (no DATABASE_URL) ----
PG_DB = os.getenv("POSTGRES_DB")
PG_HOST = os.getenv("POSTGRES_HOST")
PG_PORT = os.getenv("POSTGRES_PORT", "5432")
PG_USER = os.getenv("POSTGRES_USER")
PG_PASS = os.getenv("POSTGRES_PASSWORD")
PG_SSLMODE = os.getenv("POSTGRES_SSLMODE", "require")  # default require for Render

missing = [k for k, v in {
    "POSTGRES_DB": PG_DB,
    "POSTGRES_HOST": PG_HOST,
    "POSTGRES_USER": PG_USER,
    "POSTGRES_PASSWORD": PG_PASS,
}.items() if not v]

if missing:
    raise RuntimeError(
        f"Missing env vars for DB: {', '.join(missing)}. "
        "Please set them in your environment or .env file."
    )

# SQLAlchemy URL (explicit psycopg2 driver)
db_url = URL.create(
    drivername="postgresql+psycopg2",
    username=PG_USER,
    password=PG_PASS,
    host=PG_HOST,
    port=int(PG_PORT),
    database=PG_DB,
    query={"sslmode": PG_SSLMODE} if PG_SSLMODE else {},
)

# Inject into alembic config for both online/offline modes
config.set_main_option("sqlalchemy.url", str(db_url))

# Logging config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- Import your models' Base metadata ---
from app.models.gold import Base as GoldBase
from app.models.exchange import Base as ExchangeBase

# Merge metadata from multiple Bases
metadata = MetaData()
for m in (GoldBase.metadata, ExchangeBase.metadata):
    for t in m.tables.values():
        if t.name not in metadata.tables:
            t.tometadata(metadata)

target_metadata = metadata


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
        config.get_section(config.config_ini_section),
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
