from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


if settings.database_url.startswith("sqlite"):
    database_path = settings.database_url.removeprefix("sqlite:///")
    if database_path.startswith("./"):
        database_path = database_path[2:]
    resolved_database_path = Path(database_path)
    if not resolved_database_path.is_absolute():
        resolved_database_path = Path(__file__).resolve().parents[2] / resolved_database_path
    resolved_database_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        "sqlite:///" + resolved_database_path.as_posix(),
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_engine(settings.database_url)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
