import os


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


DEBUG = _env_bool("DEBUG", False)

# Database settings (Postgres only).
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL must be set and point to Postgres.")
if not (DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgresql+psycopg2://")):
    raise RuntimeError("DATABASE_URL must be a Postgres URL.")

ASYNC_DATABASE_URL = os.getenv("ASYNC_DATABASE_URL")
if not ASYNC_DATABASE_URL:
    if DATABASE_URL.startswith("postgresql+psycopg2://"):
        ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
    elif DATABASE_URL.startswith("postgresql://"):
        ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
    else:
        ASYNC_DATABASE_URL = DATABASE_URL

# Endpoint lock normalization rules used by EndpointLockRegistry.
# Format: list of (regex_pattern, replacement) tuples.
ENDPOINT_LOCK_NORMALIZATION_RULES: list[tuple[str, str]] = []

# SQLAlchemy model modules to import before metadata creation.
MODEL_MODULES: tuple[str, ...] = (
    "src.seedwork.access_token_repo",
    "src.iol.entities",
)

# Default schema name for relational databases (ignored for sqlite).
DB_SCHEMA = os.getenv("DB_SCHEMA", "iol")
