"""LangGraph StateGraph 定义"""
import asyncio
import logging
from langgraph.graph import END, START, StateGraph
from src.storage.database import get_db_session
from src.storage.repositories.task_repo import TaskRepository
from src.workflow.nodes.chunk_node import chunk_documents
from src.workflow.nodes.embed_node import embed_and_store
from src.workflow.nodes.error_node import handle_error
from src.workflow.nodes.llm_node import llm_analyze_pairs
from src.workflow.nodes.parse_node import parse_documents
from src.workflow.nodes.report_node import generate_report
from src.workflow.nodes.retrieve_node import retrieve_similar_pairs
from src.workflow.nodes.score_node import score_candidates
from src.workflow.nodes.structure_node import analyze_structure_and_fields
from src.workflow.nodes.whitelist_node import filter_whitelist
from src.workflow.routers import route_after_score
from src.workflow.state import TenderComparisonState

logger = logging.getLogger(__name__)


def _wrap_node(fn, node_name: str):
    def wrapped(state: TenderComparisonState) -> dict:
        try:
            result = fn(state)
            progress = result.get("processing_progress")
            task_id = state.get("task_id")
            if progress is not None and task_id:
                async def _persist():
                    async with get_db_session() as session:
                        await TaskRepository(session).update_progress(task_id, progress)
                asyncio.run(_persist())
            return result
        except Exception as e:
            logger.error(f"节点 {node_name} 执行失败: {e}", exc_info=True)
            return {"error_message": str(e), "current_node": node_name}
    wrapped.__name__ = fn.__name__
    return wrapped


def build_graph() -> StateGraph:
    graph = StateGraph(TenderComparisonState)
    graph.add_node("parse_documents", _wrap_node(parse_documents, "parse_documents"))
    graph.add_node("chunk_documents", _wrap_node(chunk_documents, "chunk_documents"))
    graph.add_node("analyze_structure_and_fields", _wrap_node(analyze_structure_and_fields, "analyze_structure_and_fields"))
    graph.add_node("filter_whitelist", _wrap_node(filter_whitelist, "filter_whitelist"))
    graph.add_node("embed_and_store", _wrap_node(embed_and_store, "embed_and_store"))
    graph.add_node("retrieve_similar_pairs", _wrap_node(retrieve_similar_pairs, "retrieve_similar_pairs"))
    graph.add_node("score_candidates", _wrap_node(score_candidates, "score_candidates"))
    graph.add_node("llm_analyze_pairs", _wrap_node(llm_analyze_pairs, "llm_analyze_pairs"))
    graph.add_node("generate_report", _wrap_node(generate_report, "generate_report"))
    graph.add_node("handle_error", handle_error)
    graph.add_edge(START, "parse_documents")
    graph.add_conditional_edges(
        "parse_documents",
        lambda s: "handle_error" if s.get("error_message") else "chunk_documents",
        {"chunk_documents": "chunk_documents", "handle_error": "handle_error"},
    )
    graph.add_edge("chunk_documents", "analyze_structure_and_fields")
    graph.add_edge("analyze_structure_and_fields", "filter_whitelist")
    graph.add_edge("filter_whitelist", "embed_and_store")
    graph.add_edge("embed_and_store", "retrieve_similar_pairs")
    graph.add_edge("retrieve_similar_pairs", "score_candidates")
    graph.add_conditional_edges(
        "score_candidates",
        route_after_score,
        {"llm_analyze_pairs": "llm_analyze_pairs", "generate_report": "generate_report"},
    )
    graph.add_edge("llm_analyze_pairs", "generate_report")
    graph.add_edge("generate_report", END)
    graph.add_edge("handle_error", END)
    return graph


def compile_graph():
    return build_graph().compile()
