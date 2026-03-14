"""SQLAlchemy 数据库配置"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


_engine = None
_session_factory = None


def get_engine(database_url: str = "sqlite+aiosqlite:///./data/tender_integrity.db"):
    global _engine
    if _engine is None:
        db_path = database_url.replace("sqlite+aiosqlite:///", "")
        if db_path and not db_path.startswith(":"):
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        _engine = create_async_engine(
            database_url,
            echo=False,
            connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
        )
        logger.info(f"数据库引擎初始化: {database_url}")
    return _engine


def get_session_factory(database_url: str | None = None):
    global _session_factory
    if _session_factory is None:
        from config.settings import settings
        url = database_url or settings.database_url
        engine = get_engine(url)
        _session_factory = async_sessionmaker(engine, expire_on_commit=False)
    return _session_factory


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db(database_url: str | None = None):
    """创建所有表"""
    from config.settings import settings
    from src.storage.models import Task, Document, RiskPair  # noqa: F401

    url = database_url or settings.database_url
    engine = get_engine(url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("数据库表初始化完成")
