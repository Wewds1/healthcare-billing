import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional for lightweight runtimes
    def load_dotenv():
        return False

load_dotenv()

DEFAULT_SQLITE_URL = "sqlite:///./healthcare_billing.db"


def resolve_database_url() -> str:
    configured_url = os.getenv("DATABASE_URL", "").strip()
    local_override = os.getenv("LOCAL_DATABASE_URL", DEFAULT_SQLITE_URL).strip()
    running_in_docker = Path("/.dockerenv").exists()

    if not configured_url:
        return local_override

    # The checked-in env uses Docker service host `db`, which does not resolve
    # for a normal local run. Fall back to a local database outside Docker.
    if "@db:" in configured_url and not running_in_docker:
        return local_override

    return configured_url


DATABASE_URL = resolve_database_url()
ENGINE_KWARGS = {"pool_pre_ping": True}

if DATABASE_URL.startswith("sqlite"):
    ENGINE_KWARGS["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **ENGINE_KWARGS)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()
