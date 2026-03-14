"""FastAPI 依赖注入"""
from config.settings import settings
from src.storage.database import get_db_session


async def get_session():
    async with get_db_session() as session:
        yield session
