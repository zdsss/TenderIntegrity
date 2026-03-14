"""报告下载端点"""
import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from src.api.dependencies import get_session
from src.storage.repositories.task_repo import TaskRepository

router = APIRouter(prefix="/tasks", tags=["reports"])


def _get_report_json(task_id: str) -> dict:
    report_path = Path(settings.report_dir) / f"report_{task_id}.json"
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="报告尚未生成")
    with open(report_path, encoding="utf-8") as f:
        return json.load(f)


@router.get("/{task_id}/report")
async def get_report(task_id: str, session: AsyncSession = Depends(get_session)):
    """获取 JSON 风险报告"""
    task_repo = TaskRepository(session)
    task = await task_repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.status != "done":
        raise HTTPException(status_code=202, detail=f"任务尚未完成，当前状态: {task.status}")

    return JSONResponse(_get_report_json(task_id))


@router.get("/{task_id}/report/csv")
async def get_report_csv(task_id: str, session: AsyncSession = Depends(get_session)):
    """导出 CSV 报告"""
    from src.report.csv_exporter import CSVExporter

    report = _get_report_json(task_id)
    csv_path = Path(settings.report_dir) / f"report_{task_id}.csv"
    CSVExporter().export(report, csv_path)

    return FileResponse(
        str(csv_path),
        media_type="text/csv",
        filename=f"report_{task_id}.csv",
    )


@router.get("/{task_id}/report/pdf")
async def get_report_pdf(task_id: str, session: AsyncSession = Depends(get_session)):
    """导出 PDF 报告"""
    from src.report.pdf_exporter import PDFExporter

    report = _get_report_json(task_id)
    pdf_path = Path(settings.report_dir) / f"report_{task_id}.pdf"
    actual_path = PDFExporter().export(report, pdf_path)

    media_type = "application/pdf" if actual_path.suffix == ".pdf" else "text/html"
    return FileResponse(
        str(actual_path),
        media_type=media_type,
        filename=actual_path.name,
    )
