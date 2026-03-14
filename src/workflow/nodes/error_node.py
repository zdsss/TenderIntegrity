"""handle_error 节点"""
import logging
from src.workflow.state import TenderComparisonState

logger = logging.getLogger(__name__)


def handle_error(state: TenderComparisonState) -> dict:
    error_msg = state.get("error_message", "未知错误")
    logger.error(f"工作流错误 (task={state['task_id']}): {error_msg}")
    return {
        "report": {"task_id": state["task_id"], "status": "error", "error_message": error_msg},
        "overall_risk_level": "low",
        "overall_similarity_rate": 0.0,
        "current_node": "handle_error",
        "processing_progress": 1.0,
    }
