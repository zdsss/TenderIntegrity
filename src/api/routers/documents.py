"""文件上传端点"""
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from src.api.dependencies import get_session
from src.api.schemas.document import DocumentUploadResponse
from src.storage.repositories.document_repo import DocumentRepository

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
):
    """上传标书文件（PDF/Word/TXT）"""
    allowed_types = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
        "text/plain",
    }

    ext = Path(file.filename or "").suffix.lower()
    if ext not in {".pdf", ".docx", ".doc", ".txt"}:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {ext}")

    doc_id = str(uuid.uuid4())
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = upload_dir / f"{doc_id}{ext}"
    content = await file.read()

    with open(file_path, "wb") as f:
        f.write(content)

    return DocumentUploadResponse(
        doc_id=doc_id,
        filename=file.filename or "unknown",
        file_size=len(content),
    )
