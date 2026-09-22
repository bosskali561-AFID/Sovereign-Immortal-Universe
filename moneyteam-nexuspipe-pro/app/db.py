from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import get_settings


class Base(DeclarativeBase):
    pass


_engine_obj = None
SessionLocal = None


def get_engine():
    global _engine_obj, SessionLocal
    if _engine_obj is None:
        settings = get_settings()
        connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
        _engine_obj = create_engine(settings.database_url, connect_args=connect_args, pool_pre_ping=True)
        SessionLocal = sessionmaker(bind=_engine_obj, autoflush=False, autocommit=False)
    return _engine_obj


def init_db():
    from . import models  # noqa: F401  (registers ORM mappings)

    Base.metadata.create_all(get_engine())


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
