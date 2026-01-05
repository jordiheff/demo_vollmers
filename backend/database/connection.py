"""
Database connection management for SQLite.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from config import settings


# Ensure data directory exists
db_dir = os.path.dirname(settings.sqlite_db_path)
if db_dir and not os.path.exists(db_dir):
    os.makedirs(db_dir)

# Create SQLite engine
DATABASE_URL = f"sqlite:///{settings.sqlite_db_path}"
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI routes to get database session.

    Yields:
        SQLAlchemy Session object
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize the database, creating all tables.
    """
    from .models import Base
    Base.metadata.create_all(bind=engine)
