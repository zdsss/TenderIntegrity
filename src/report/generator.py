"""ReportGenerator：汇总 → 报告结构"""
import logging
from pathlib import Path

from src.report.csv_exporter import CSVExporter
from src.report.json_exporter import JSONExporter
from src.report.pdf_exporter import PDFExporter

logger = logging.getLogger(__name__)


class ReportGenerator:
    """统一报告生成入口"""

    def __init__(self, output_dir: str | Path = "./data/reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_all(self, report: dict, task_id: str) -> dict[str, Path]:
        """导出 JSON + CSV + PDF 三种格式"""
        paths = {}

        json_path = self.output_dir / f"report_{task_id}.json"
        paths["json"] = JSONExporter().export(report, json_path)

        csv_path = self.output_dir / f"report_{task_id}.csv"
        paths["csv"] = CSVExporter().export(report, csv_path)

        pdf_path = self.output_dir / f"report_{task_id}.pdf"
        paths["pdf"] = PDFExporter().export(report, pdf_path)

        logger.info(f"报告导出完成: {list(paths.values())}")
        return paths

    def export_json(self, report: dict, task_id: str) -> Path:
        json_path = self.output_dir / f"report_{task_id}.json"
        return JSONExporter().export(report, json_path)

    def export_csv(self, report: dict, task_id: str) -> Path:
        csv_path = self.output_dir / f"report_{task_id}.csv"
        return CSVExporter().export(report, csv_path)
