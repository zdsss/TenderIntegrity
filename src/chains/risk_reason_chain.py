"""RiskReasonChain：LCEL 风险判定理由生成链"""
import json
import logging
import re

from src.analysis.scorer import SimilarPair
from src.chains.output_parsers import RiskAnalysisOutput
from src.chains.prompts.risk_analysis import risk_analysis_prompt

logger = logging.getLogger(__name__)

MAX_CHUNK_CHARS = 800


def _truncate(text: str, max_chars: int = MAX_CHUNK_CHARS) -> str:
    """截断过长文本"""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "…（已截断）"


def _parse_llm_output(content: str) -> RiskAnalysisOutput:
    """从 LLM 输出中解析 JSON"""
    # 提取 JSON 块
    json_match = re.search(r"\{.*\}", content, re.DOTALL)
    if not json_match:
        raise ValueError(f"LLM 输出中未找到 JSON: {content[:200]}")

    data = json.loads(json_match.group())
    return RiskAnalysisOutput(**data)


class RiskReasonChain:
    """
    风险判定理由生成链
    使用 LCEL: prompt → LLM → parser
    支持 Anthropic Claude 和阿里云百炼（OpenAI 兼容）
    """

    def __init__(
        self,
        model: str = "claude-sonnet-4-6",
        temperature: float = 0.1,
        max_tokens: int = 1024,
        anthropic_api_key: str | None = None,
        provider: str = "anthropic",
        openai_api_key: str | None = None,
        openai_base_url: str | None = None,
    ):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.anthropic_api_key = anthropic_api_key
        self.provider = provider
        self.openai_api_key = openai_api_key
        self.openai_base_url = openai_base_url
        self._llm = None

    def _get_llm(self):
        if self._llm is None:
            if self.provider == "dashscope":
                try:
                    from langchain_openai import ChatOpenAI
                except ImportError:
                    raise ImportError("请安装 langchain-openai: uv add langchain-openai")
                self._llm = ChatOpenAI(
                    model=self.model,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    api_key=self.openai_api_key,
                    base_url=self.openai_base_url,
                )
            else:
                try:
                    from langchain_anthropic import ChatAnthropic
                except ImportError:
                    raise ImportError("请安装 langchain-anthropic: uv add langchain-anthropic")
                kwargs = dict(
                    model=self.model,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
                if self.anthropic_api_key:
                    kwargs["anthropic_api_key"] = self.anthropic_api_key
                self._llm = ChatAnthropic(**kwargs)
        return self._llm

    def analyze_pair(
        self,
        pair: SimilarPair,
        doc_a_name: str = "文档A",
        doc_b_name: str = "文档B",
    ) -> RiskAnalysisOutput | None:
        """分析一个相似对，返回结构化输出（失败返回 None）"""
        try:
            llm = self._get_llm()
            chain = risk_analysis_prompt | llm

            result = chain.invoke(
                {
                    "doc_a_name": doc_a_name,
                    "section_a": pair.chunk_a.section_title or "未知章节",
                    "text_a": _truncate(pair.chunk_a.text),
                    "doc_b_name": doc_b_name,
                    "section_b": pair.chunk_b.section_title or "未知章节",
                    "text_b": _truncate(pair.chunk_b.text),
                    "vector_similarity": pair.vector_similarity,
                    "keyword_overlap": pair.keyword_overlap,
                    "base_risk_score": pair.base_risk_score,
                }
            )

            output = _parse_llm_output(result.content)
            logger.debug(f"LLM 分析完成 pair={pair.pair_id}: {output.risk_level}")
            return output

        except Exception as e:
            logger.error(f"LLM 分析失败 pair={pair.pair_id}: {e}")
            return None

    def batch_analyze(
        self,
        pairs: list[SimilarPair],
        doc_names: dict[str, str],
    ) -> list[SimilarPair]:
        """批量分析相似对，更新 pair 的 LLM 分析结果"""
        from src.analysis.scorer import RiskScorer

        scorer = RiskScorer()
        doc_ids = list(doc_names.keys())
        doc_a_name = doc_names.get(doc_ids[0], "文档A") if doc_ids else "文档A"
        doc_b_name = doc_names.get(doc_ids[1], "文档B") if len(doc_ids) > 1 else "文档B"

        for pair in pairs:
            output = self.analyze_pair(pair, doc_a_name, doc_b_name)
            if output:
                pair.risk_level = output.risk_level
                pair.risk_type = output.risk_type
                pair.confidence = output.confidence
                pair.reason_zh = output.reason_zh
                pair.evidence_quote_a = output.evidence_quote_a
                pair.evidence_quote_b = output.evidence_quote_b
                pair.suggest_action = output.suggest_action
                scorer.apply_llm_adjustment(pair, output.score_adjustment)

        return pairs
