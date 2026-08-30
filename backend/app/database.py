import os
from sqlmodel import SQLModel, Session, create_engine

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./support_platform.db")

# Render gives postgresql:// but SQLAlchemy needs postgresql+psycopg2://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

# Connection pool args only for PostgreSQL (SQLite doesn't support them)
connect_args = {}
engine_kwargs = {}
if "sqlite" in DATABASE_URL:
    connect_args = {"check_same_thread": False}
else:
    engine_kwargs = {"pool_pre_ping": True, "pool_size": 5, "max_overflow": 10}

engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args, **engine_kwargs)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
