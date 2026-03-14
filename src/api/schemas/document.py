"""文档相关 Pydantic 模型"""
from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    doc_id: str
    filename: str
    file_size: int
    message: str = "上传成功"
