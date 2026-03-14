"""文档仓库"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.storage.models import Document


class DocumentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        task_id: str,
        doc_id: str,
        doc_role: str,
        filename: str,
        file_path: str,
        file_size: int | None = None,
    ) -> Document:
        doc = Document(
            id=doc_id,
            task_id=task_id,
            doc_role=doc_role,
            filename=filename,
            file_path=file_path,
            file_size=file_size,
        )
        self.session.add(doc)
        await self.session.flush()
        return doc

    async def update_chunk_count(self, doc_id: str, count: int) -> None:
        result = await self.session.execute(select(Document).where(Document.id == doc_id))
        doc = result.scalar_one_or_none()
        if doc:
            doc.chunk_count = count

    async def get_by_task(self, task_id: str) -> list[Document]:
        result = await self.session.execute(
            select(Document).where(Document.task_id == task_id)
        )
        return list(result.scalars().all())
