"""
Database session management for MySQL using SQLAlchemy.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


def _engine_config(database_url: str) -> tuple[str, dict]:
    """Translate Aiven-style SSL URL options into PyMySQL connect args."""
    url = make_url(database_url)
    ssl_mode = url.query.get("ssl-mode") or url.query.get("ssl_mode")

    options: dict = {"pool_pre_ping": True}
    if ssl_mode and str(ssl_mode).upper() != "DISABLED":
        options["connect_args"] = {"ssl": {}}
        url = url.difference_update_query(["ssl-mode", "ssl_mode"])

    return url.render_as_string(hide_password=False), options


database_url, engine_options = _engine_config(settings.database_url)


engine = create_engine(
    database_url,
    **engine_options,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,  # MySQL connections auto-close after 8hrs — recycle after 1hr
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a DB session and ensures it's closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
