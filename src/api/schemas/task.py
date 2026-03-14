"""任务相关 Pydantic 模型"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class TaskCreateRequest(BaseModel):
    doc_ids: list[str]
    comparison_mode: Literal["pairwise", "all_vs_all"] = "pairwise"


class TaskResponse(BaseModel):
    task_id: str
    status: str
    progress: float
    overall_risk_level: str | None = None
    overall_similarity_rate: float | None = None
    error_message: str | None = None
    created_at: datetime | None = None
