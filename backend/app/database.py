"""SQLAlchemy database engine and session management."""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import settings

# Ensure data directory exists
os.makedirs(os.path.dirname(settings.SQLITE_PATH), exist_ok=True)

SQLALCHEMY_DATABASE_URL = f"sqlite:///{settings.SQLITE_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables. Imported models register themselves on Base."""
    from . import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
