from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


DATABASE_URL = settings.database_url


class Base(DeclarativeBase):
    pass


def _create_engine(database_url: str) -> Engine:
    connect_args = {}

    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    return create_engine(
        database_url,
        connect_args=connect_args,
    )


engine = _create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


def configure_database(database_url: str) -> None:
    """切换数据库连接，主要供自动化测试使用。"""
    global DATABASE_URL, engine, SessionLocal

    engine.dispose()

    DATABASE_URL = database_url
    engine = _create_engine(DATABASE_URL)

    SessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )


def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()


def init_database() -> None:
    # 导入模型后，SQLAlchemy 才能知道需要创建哪些数据表。
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)