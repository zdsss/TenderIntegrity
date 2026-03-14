"""SQLAlchemy ORM 模型"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.storage.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending/running/done/error
    comparison_mode: Mapped[str] = mapped_column(String(20), default="pairwise")
    overall_risk_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    overall_similarity_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    documents: Mapped[list["Document"]] = relationship(back_populates="task", cascade="all, delete-orphan")
    risk_pairs: Mapped[list["RiskPair"]] = relationship(back_populates="task", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))
    doc_role: Mapped[str] = mapped_column(String(20), default="doc_a")  # doc_a / doc_b / ...
    filename: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(512))
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    task: Mapped["Task"] = relationship(back_populates="documents")


class RiskPair(Base):
    __tablename__ = "risk_pairs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))
    pair_id: Mapped[str] = mapped_column(String(32))
    risk_level: Mapped[str] = mapped_column(String(20))
    risk_type: Mapped[str] = mapped_column(String(50), default="normal_overlap")
    final_score: Mapped[float] = mapped_column(Float)
    vector_similarity: Mapped[float] = mapped_column(Float)
    keyword_overlap: Mapped[float] = mapped_column(Float, default=0.0)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    doc_a_id: Mapped[str] = mapped_column(String(36))
    doc_b_id: Mapped[str] = mapped_column(String(36))
    chunk_a_id: Mapped[str] = mapped_column(String(64))
    chunk_b_id: Mapped[str] = mapped_column(String(64))
    section_a: Mapped[str] = mapped_column(String(255), default="")
    section_b: Mapped[str] = mapped_column(String(255), default="")
    text_a: Mapped[str] = mapped_column(Text, default="")
    text_b: Mapped[str] = mapped_column(Text, default="")
    reason_zh: Mapped[str] = mapped_column(Text, default="")
    suggest_action: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    task: Mapped["Task"] = relationship(back_populates="risk_pairs")
