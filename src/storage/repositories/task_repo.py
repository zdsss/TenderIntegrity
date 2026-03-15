"""任务仓库"""
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.storage.models import Task

logger = logging.getLogger(__name__)


class TaskRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, task_id: str, comparison_mode: str = "pairwise") -> Task:
        task = Task(id=task_id, comparison_mode=comparison_mode)
        self.session.add(task)
        await self.session.flush()
        return task

    async def get(self, task_id: str) -> Task | None:
        result = await self.session.execute(select(Task).where(Task.id == task_id))
        return result.scalar_one_or_none()

    async def update_progress(self, task_id: str, progress: float) -> None:
        task = await self.get(task_id)
        if task:
            task.progress = progress

    async def update_status(self, task_id: str, status: str, progress: float = 0.0) -> None:
        task = await self.get(task_id)
        if task:
            task.status = status
            task.progress = progress

    async def update_result(
        self,
        task_id: str,
        overall_risk_level: str,
        overall_similarity_rate: float,
    ) -> None:
        task = await self.get(task_id)
        if task:
            task.status = "done"
            task.progress = 1.0
            task.overall_risk_level = overall_risk_level
            task.overall_similarity_rate = overall_similarity_rate

    async def set_error(self, task_id: str, error_message: str) -> None:
        task = await self.get(task_id)
        if task:
            task.status = "error"
            task.error_message = error_message

    async def list_all(self, offset: int = 0, limit: int = 20) -> list[Task]:
        result = await self.session.execute(
            select(Task).order_by(Task.created_at.desc()).offset(offset).limit(limit)
        )
        return list(result.scalars().all())

    async def delete(self, task_id: str) -> bool:
        task = await self.get(task_id)
        if task:
            await self.session.delete(task)
            return True
        return False
