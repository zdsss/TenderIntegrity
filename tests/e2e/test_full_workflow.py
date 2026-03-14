"""端到端工作流测试（需要完整环境）"""
import pytest
from pathlib import Path


@pytest.mark.e2e
def test_full_comparison_workflow(sample_docx_a, sample_docx_b, tmp_path):
    """使用测试文档跑完整工作流"""
    import uuid
    from src.workflow.graph import compile_graph
    from src.workflow.state import TenderComparisonState

    task_id = str(uuid.uuid4())[:8]
    graph = compile_graph()

    initial_state: TenderComparisonState = {
        "task_id": task_id,
        "doc_ids": ["doc_a", "doc_b"],
        "file_paths": {"doc_a": str(sample_docx_a), "doc_b": str(sample_docx_b)},
        "doc_names": {"doc_a": sample_docx_a.name, "doc_b": sample_docx_b.name},
        "comparison_mode": "pairwise",
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

    final_state = graph.invoke(initial_state)

    # 基本验证
    assert final_state.get("error_message") is None, f"工作流报错: {final_state.get('error_message')}"
    assert final_state.get("report") is not None
    assert final_state.get("overall_risk_level") in ("high", "medium", "low")
    assert 0.0 <= final_state.get("overall_similarity_rate", 0) <= 1.0

    report = final_state["report"]
    assert "task_id" in report
    assert "risk_pairs" in report
    assert "risk_summary" in report

    # 导出报告
    from src.report.generator import ReportGenerator
    generator = ReportGenerator(tmp_path)
    paths = generator.export_json(report, task_id)
    assert paths.exists()
    assert paths.stat().st_size > 0

    print(f"\n✅ E2E 测试通过！")
    print(f"   整体风险等级: {final_state['overall_risk_level']}")
    print(f"   整体雷同率: {final_state['overall_similarity_rate']:.1%}")
    print(f"   风险对数量: {len(report.get('risk_pairs', []))}")
