"""比对任务端点"""
import asyncio
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from src.api.dependencies import get_session
from src.api.schemas.task import TaskCreateRequest, TaskResponse
from src.storage.database import get_db_session
from src.storage.repositories.document_repo import DocumentRepository
from src.storage.repositories.task_repo import TaskRepository

router = APIRouter(prefix="/tasks", tags=["tasks"])


async def _run_workflow(task_id: str, doc_ids: list[str], comparison_mode: str):
    """在后台运行工作流"""
    from src.workflow.graph import compile_graph
    from src.workflow.state import TenderComparisonState

    async with get_db_session() as session:
        task_repo = TaskRepository(session)
        await task_repo.update_status(task_id, "running", 0.05)

    # 查询文件路径
    async with get_db_session() as session:
        doc_repo = DocumentRepository(session)
        upload_dir = Path(settings.upload_dir)

        file_paths = {}
        doc_names = {}
        for doc_id in doc_ids:
            # 查找上传文件
            for ext in [".pdf", ".docx", ".doc", ".txt"]:
                fp = upload_dir / f"{doc_id}{ext}"
                if fp.exists():
                    file_paths[doc_id] = str(fp)
                    doc_names[doc_id] = fp.name
                    break

    if len(file_paths) < 2:
        async with get_db_session() as session:
            task_repo = TaskRepository(session)
            await task_repo.set_error(task_id, f"文件不足: {list(file_paths.keys())}")
        return

    graph = compile_graph()
    initial_state: TenderComparisonState = {
        "task_id": task_id,
        "doc_ids": doc_ids,
        "file_paths": file_paths,
        "doc_names": doc_names,
        "comparison_mode": comparison_mode,
        "raw_texts": {},
        "chunks": {},
        "embeddings_stored": False,
        "candidate_pairs": [],
        "scored_pairs": [],
        "llm_analyzed_pairs": [],
        "current_node": "start",
        "error_message": None,
        "processing_progress": 0.0,
        "report": None,
        "overall_risk_level": "low",
        "overall_similarity_rate": 0.0,
    }

    try:
        final_state = await asyncio.to_thread(graph.invoke, initial_state)

        async with get_db_session() as session:
            task_repo = TaskRepository(session)
            if final_state.get("error_message"):
                await task_repo.set_error(task_id, final_state["error_message"])
            else:
                await task_repo.update_result(
                    task_id,
                    final_state.get("overall_risk_level", "low"),
                    final_state.get("overall_similarity_rate", 0.0),
                )

            # 保存报告到文件
            if final_state.get("report"):
                from src.report.generator import ReportGenerator
                generator = ReportGenerator(settings.report_dir)
                generator.export_json(final_state["report"], task_id)

    except Exception as e:
        async with get_db_session() as session:
            task_repo = TaskRepository(session)
            await task_repo.set_error(task_id, str(e))


@router.post("", response_model=TaskResponse, status_code=201)
async def create_task(
    request: TaskCreateRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    """创建比对任务并在后台运行"""
    if len(request.doc_ids) < 2:
        raise HTTPException(status_code=400, detail="至少需要 2 份文档")

    task_id = str(uuid.uuid4())
    task_repo = TaskRepository(session)
    task = await task_repo.create(task_id, request.comparison_mode)

    background_tasks.add_task(
        _run_workflow, task_id, request.doc_ids, request.comparison_mode
    )

    return TaskResponse(
        task_id=task.id,
        status=task.status,
        progress=task.progress,
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, session: AsyncSession = Depends(get_session)):
    """查询任务状态"""
    task_repo = TaskRepository(session)
    task = await task_repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return TaskResponse(
        task_id=task.id,
        status=task.status,
        progress=task.progress,
        overall_risk_level=task.overall_risk_level,
        overall_similarity_rate=task.overall_similarity_rate,
        error_message=task.error_message,
        created_at=task.created_at,
    )


@router.get("", response_model=list[TaskResponse])
async def list_tasks(
    offset: int = 0,
    limit: int = 20,
    session: AsyncSession = Depends(get_session),
):
    """历史任务列表"""
    task_repo = TaskRepository(session)
    tasks = await task_repo.list_all(offset=offset, limit=limit)
    return [
        TaskResponse(
            task_id=t.id,
            status=t.status,
            progress=t.progress,
            overall_risk_level=t.overall_risk_level,
            overall_similarity_rate=t.overall_similarity_rate,
            created_at=t.created_at,
        )
        for t in tasks
    ]


@router.delete("/{task_id}", status_code=204)
async def delete_task(task_id: str, session: AsyncSession = Depends(get_session)):
    """删除任务及数据"""
    task_repo = TaskRepository(session)
    deleted = await task_repo.delete(task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="任务不存在")
