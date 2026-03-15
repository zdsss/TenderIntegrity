"""RiskReasonChain：LCEL 风险判定理由生成链（含三级降级 + 重试）"""
import json
import logging
import re

from src.analysis.scorer import SimilarPair
from src.chains.output_parsers import RiskAnalysisOutput
from src.chains.prompts.risk_analysis import risk_analysis_prompt

logger = logging.getLogger(__name__)

MAX_CHUNK_CHARS = 800

# 全量失败时的默认输出
_FALLBACK_OUTPUT = RiskAnalysisOutput(
    risk_level="none",
    risk_type="normal_overlap",
    confidence=0.0,
    reason_zh="LLM 分析失败，当前结果仅基于向量相似度评分，无语义判定。",
    score_adjustment=0.0,
)


def _truncate(text: str, max_chars: int = MAX_CHUNK_CHARS) -> str:
    """截断过长文本"""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "…（已截断）"


def _parse_llm_output(content: str) -> RiskAnalysisOutput:
    """从 LLM 输出中解析 JSON（第2级降级）"""
    json_match = re.search(r"\{.*\}", content, re.DOTALL)
    if not json_match:
        raise ValueError(f"LLM 输出中未找到 JSON: {content[:200]}")
    data = json.loads(json_match.group())
    return RiskAnalysisOutput(**data)


class RiskReasonChain:
    """
    风险判定理由生成链
    使用 LCEL: prompt → LLM → parser

    可靠性策略：
    Level 1: with_structured_output（LangChain 原生，最可靠）
    Level 2: 正则 JSON 提取 + Pydantic 解析（兼容旧模型）
    Level 3: 默认值（保证工作流不崩溃）
    每级最多重试 2 次。
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
                    raise ImportError(
                        "请安装 langchain-anthropic: uv add langchain-anthropic"
                    )
                kwargs = dict(
                    model=self.model,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
                if self.anthropic_api_key:
                    kwargs["anthropic_api_key"] = self.anthropic_api_key
                self._llm = ChatAnthropic(**kwargs)
        return self._llm

    def _build_inputs(
        self,
        pair: SimilarPair,
        doc_a_name: str,
        doc_b_name: str,
    ) -> dict:
        return {
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

    def _try_structured_output(self, inputs: dict) -> RiskAnalysisOutput:
        """Level 1：with_structured_output（最多重试 2 次）"""
        llm = self._get_llm()
        structured_llm = llm.with_structured_output(RiskAnalysisOutput)
        chain = risk_analysis_prompt | structured_llm
        last_exc: Exception | None = None
        for attempt in range(3):
            try:
                result = chain.invoke(inputs)
                if isinstance(result, RiskAnalysisOutput):
                    return result
                # 某些模型返回 dict
                if isinstance(result, dict):
                    return RiskAnalysisOutput(**result)
                raise ValueError(f"意外返回类型: {type(result)}")
            except Exception as e:
                last_exc = e
                logger.warning(
                    f"[structured_output] 第 {attempt + 1} 次失败: {e}"
                )
        raise last_exc  # type: ignore[misc]

    def _try_regex_parse(self, inputs: dict) -> RiskAnalysisOutput:
        """Level 2：正则 JSON 解析（最多重试 2 次）"""
        llm = self._get_llm()
        chain = risk_analysis_prompt | llm
        last_exc: Exception | None = None
        for attempt in range(3):
            try:
                result = chain.invoke(inputs)
                return _parse_llm_output(result.content)
            except Exception as e:
                last_exc = e
                logger.warning(f"[regex_parse] 第 {attempt + 1} 次失败: {e}")
        raise last_exc  # type: ignore[misc]

    def analyze_pair(
        self,
        pair: SimilarPair,
        doc_a_name: str = "文档A",
        doc_b_name: str = "文档B",
    ) -> RiskAnalysisOutput:
        """
        分析一个相似对，返回结构化输出。
        三级降级保证永不崩溃：Level1 → Level2 → 默认值。
        """
        inputs = self._build_inputs(pair, doc_a_name, doc_b_name)

        # Level 1
        try:
            output = self._try_structured_output(inputs)
            logger.debug(f"LLM(L1) 分析完成 pair={pair.pair_id}: {output.risk_level}")
            return output
        except Exception as e:
            logger.warning(f"Level1(structured_output) 全部失败 pair={pair.pair_id}: {e}")

        # Level 2
        try:
            output = self._try_regex_parse(inputs)
            logger.debug(f"LLM(L2) 分析完成 pair={pair.pair_id}: {output.risk_level}")
            return output
        except Exception as e:
            logger.error(f"Level2(regex_parse) 全部失败 pair={pair.pair_id}: {e}")

        # Level 3：默认值，保证工作流继续
        logger.error(f"LLM 三级降级均失败，使用默认值 pair={pair.pair_id}")
        return _FALLBACK_OUTPUT

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
            # 降级兜底：仅当不是默认 fallback 时更新风险等级
            if output.reason_zh != _FALLBACK_OUTPUT.reason_zh:
                pair.risk_level = output.risk_level
                pair.risk_type = output.risk_type
                pair.confidence = output.confidence
                pair.evidence_quote_a = output.evidence_quote_a
                pair.evidence_quote_b = output.evidence_quote_b
                pair.suggest_action = output.suggest_action
                scorer.apply_llm_adjustment(pair, output.score_adjustment)
            # reason_zh 始终更新（包括失败时的说明）
            pair.reason_zh = output.reason_zh

        return pairs
