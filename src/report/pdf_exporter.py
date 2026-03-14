"""PDF 报告生成（WeasyPrint）"""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>标书雷同风险报告</title>
<style>
body {{ font-family: "Source Han Sans", "Noto Sans CJK SC", sans-serif; font-size: 12px; color: #333; }}
h1 {{ color: #1a1a2e; font-size: 20px; border-bottom: 2px solid #1a1a2e; padding-bottom: 8px; }}
h2 {{ color: #16213e; font-size: 15px; margin-top: 20px; }}
.summary {{ background: #f0f4ff; padding: 12px; border-radius: 6px; margin-bottom: 20px; }}
.summary .risk-high {{ color: #c0392b; font-weight: bold; font-size: 16px; }}
.summary .risk-medium {{ color: #d35400; font-weight: bold; font-size: 16px; }}
.summary .risk-low {{ color: #27ae60; font-weight: bold; font-size: 16px; }}
.pair {{ border: 1px solid #ddd; margin-bottom: 16px; border-radius: 4px; }}
.pair-header {{ padding: 8px 12px; font-weight: bold; }}
.pair-header.high {{ background: #fde8e8; }}
.pair-header.medium {{ background: #fef3e2; }}
.pair-header.low {{ background: #e8f5e9; }}
.pair-body {{ padding: 10px 12px; }}
.text-compare {{ display: flex; gap: 12px; }}
.text-box {{ flex: 1; background: #f9f9f9; padding: 8px; border-left: 3px solid #999; font-size: 11px; }}
.reason {{ margin-top: 8px; padding: 8px; background: #fff8e1; border-radius: 4px; }}
</style>
</head>
<body>
<h1>标书雷同风险分析报告</h1>
<div class="summary">
  <p><strong>任务 ID：</strong>{task_id}</p>
  <p><strong>整体风险等级：</strong><span class="{risk_class}">{overall_risk_level_zh}</span></p>
  <p><strong>整体雷同率：</strong>{overall_similarity_rate_pct}</p>
  <p><strong>风险统计：</strong>高风险 {high_count} 对 | 中风险 {medium_count} 对 | 低风险 {low_count} 对</p>
</div>
<h2>风险段落详情</h2>
{pairs_html}
</body>
</html>
"""

_PAIR_TEMPLATE = """
<div class="pair">
  <div class="pair-header {risk_class}">
    [{risk_level_zh}] {risk_type_zh} — 综合得分: {final_score:.1f} | 向量相似度: {vector_similarity:.1%}
  </div>
  <div class="pair-body">
    <div class="text-compare">
      <div class="text-box">
        <strong>文档A · {section_a}</strong> (第{page_a}页)<br><br>{text_a}
      </div>
      <div class="text-box">
        <strong>文档B · {section_b}</strong> (第{page_b}页)<br><br>{text_b}
      </div>
    </div>
    <div class="reason"><strong>判定理由：</strong>{reason_zh}</div>
    {suggest_action_html}
  </div>
</div>
"""

RISK_LEVEL_ZH = {"high": "高风险", "medium": "中风险", "low": "低风险", "none": "无风险"}
RISK_TYPE_ZH = {
    "verbatim_copy": "逐字抄袭",
    "semantic_paraphrase": "语义改写",
    "template_reuse": "模板复用",
    "key_param_duplicate": "关键参数雷同",
    "normal_overlap": "正常重叠",
}


class PDFExporter:
    def export(self, report: dict, output_path: str | Path) -> Path:
        """导出 PDF 报告"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        html = self._build_html(report)

        try:
            import weasyprint
            weasyprint.HTML(string=html).write_pdf(str(output_path))
        except (ImportError, OSError, Exception) as e:
            # 降级：保存 HTML 文件（WeasyPrint 未安装或缺少系统依赖库）
            html_path = output_path.with_suffix(".html")
            html_path.write_text(html, encoding="utf-8")
            logger.warning(f"PDF 导出不可用（{type(e).__name__}: {e}），已导出 HTML 报告: {html_path}")
            return html_path

        logger.info(f"PDF 报告已导出: {output_path}")
        return output_path

    def _build_html(self, report: dict) -> str:
        overall = report.get("overall_risk_level", "low")
        risk_class = f"risk-{overall}"
        summary = report.get("risk_summary", {})

        pairs_html = ""
        for pair in report.get("risk_pairs", []):
            rl = pair.get("risk_level", "low")
            suggest = pair.get("suggest_action", "")
            suggest_html = f'<div class="reason"><strong>建议：</strong>{suggest}</div>' if suggest else ""
            pairs_html += _PAIR_TEMPLATE.format(
                risk_class=rl,
                risk_level_zh=RISK_LEVEL_ZH.get(rl, rl),
                risk_type_zh=RISK_TYPE_ZH.get(pair.get("risk_type", ""), pair.get("risk_type", "")),
                final_score=pair.get("final_score", 0),
                vector_similarity=pair.get("vector_similarity", 0),
                section_a=pair.get("doc_a", {}).get("section", ""),
                page_a=pair.get("doc_a", {}).get("page", 0),
                text_a=pair.get("doc_a", {}).get("text", "")[:300],
                section_b=pair.get("doc_b", {}).get("section", ""),
                page_b=pair.get("doc_b", {}).get("page", 0),
                text_b=pair.get("doc_b", {}).get("text", "")[:300],
                reason_zh=pair.get("reason_zh", ""),
                suggest_action_html=suggest_html,
            )

        return _HTML_TEMPLATE.format(
            task_id=report.get("task_id", ""),
            risk_class=risk_class,
            overall_risk_level_zh=RISK_LEVEL_ZH.get(overall, overall),
            overall_similarity_rate_pct=f"{report.get('overall_similarity_rate', 0):.1%}",
            high_count=summary.get("high_count", 0),
            medium_count=summary.get("medium_count", 0),
            low_count=summary.get("low_count", 0),
            pairs_html=pairs_html,
        )
