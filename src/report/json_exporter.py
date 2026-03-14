"""JSON 格式报告导出"""
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class JSONExporter:
    def export(self, report: dict, output_path: str | Path) -> Path:
        """导出 JSON 报告"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"JSON 报告已导出: {output_path}")
        return output_path
