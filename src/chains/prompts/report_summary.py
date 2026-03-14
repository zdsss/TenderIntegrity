"""整体摘要生成 Prompt"""
from langchain_core.prompts import ChatPromptTemplate

SYSTEM_PROMPT = """你是一名专业的医疗采购监管审查员。请根据标书比对分析结果，生成一份简洁的中文风险摘要报告。"""

HUMAN_PROMPT = """以下是标书比对任务的分析结果，请生成一段简洁的风险摘要（200字以内）：

- 整体风险等级：{overall_risk_level}
- 整体雷同率：{overall_similarity_rate:.1%}
- 高风险段落对数：{high_count}
- 中风险段落对数：{medium_count}
- 低风险段落对数：{low_count}

主要高风险段落：
{high_risk_summary}

请生成一段简洁、专业的中文风险摘要："""

report_summary_prompt = ChatPromptTemplate.from_messages(
    [("system", SYSTEM_PROMPT), ("human", HUMAN_PROMPT)]
)
