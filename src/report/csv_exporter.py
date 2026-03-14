"""CSV 格式报告导出（pandas）"""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class CSVExporter:
    def export(self, report: dict, output_path: str | Path) -> Path:
        """导出 CSV 风险对清单"""
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("请安装 pandas: uv add pandas")

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        risk_pairs = report.get("risk_pairs", [])
        if not risk_pairs:
            rows = []
        else:
            rows = []
            for pair in risk_pairs:
                rows.append(
                    {
                        "pair_id": pair.get("pair_id", ""),
                        "risk_level": pair.get("risk_level", ""),
                        "risk_type": pair.get("risk_type", ""),
                        "final_score": pair.get("final_score", 0),
                        "vector_similarity": pair.get("vector_similarity", 0),
                        "keyword_overlap": pair.get("keyword_overlap", 0),
                        "doc_a_section": pair.get("doc_a", {}).get("section", ""),
                        "doc_a_page": pair.get("doc_a", {}).get("page", 0),
                        "doc_a_text": pair.get("doc_a", {}).get("text", "")[:200],
                        "doc_b_section": pair.get("doc_b", {}).get("section", ""),
                        "doc_b_page": pair.get("doc_b", {}).get("page", 0),
                        "doc_b_text": pair.get("doc_b", {}).get("text", "")[:200],
                        "reason_zh": pair.get("reason_zh", ""),
                        "suggest_action": pair.get("suggest_action", ""),
                        "confidence": pair.get("confidence", 0),
                    }
                )

        df = pd.DataFrame(rows)
        df.to_csv(output_path, index=False, encoding="utf-8-sig")  # utf-8-sig 支持 Excel 打开
        logger.info(f"CSV 报告已导出: {output_path}, {len(rows)} 条风险对")
        return output_path
