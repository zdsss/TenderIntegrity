"""jieba 分词 + 关键词提取"""
import logging
import re

logger = logging.getLogger(__name__)

# 停用词
STOPWORDS = {
    "的", "了", "和", "是", "在", "我", "有", "就", "不", "人", "都", "一",
    "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着",
    "没有", "看", "好", "自己", "这", "那", "这个", "那个", "但", "与",
    "及", "或", "等", "对", "以", "为", "因", "所", "如", "其", "而",
    "时", "中", "将", "进行", "提供", "需要", "应当", "应该", "必须",
    "可以", "要求", "按照", "根据", "通过", "相关", "具体", "以上",
}


class KeywordExtractor:
    """使用 jieba 提取中文文本关键词"""

    def __init__(self):
        self._initialized = False

    def _ensure_init(self):
        if not self._initialized:
            try:
                import jieba
                import jieba.analyse
                jieba.setLogLevel(logging.WARNING)
                self._initialized = True
            except ImportError:
                raise ImportError("请安装 jieba: uv add jieba")

    def extract_keywords(self, text: str, topk: int = 20) -> set[str]:
        """提取文本关键词（TF-IDF）"""
        self._ensure_init()
        import jieba.analyse

        keywords = jieba.analyse.extract_tags(text, topK=topk, withWeight=False)
        return {kw for kw in keywords if kw not in STOPWORDS and len(kw) >= 2}

    def tokenize(self, text: str) -> list[str]:
        """分词"""
        self._ensure_init()
        import jieba

        tokens = jieba.lcut(text)
        return [t for t in tokens if t.strip() and t not in STOPWORDS and len(t) >= 2]

    def jaccard_similarity(self, text_a: str, text_b: str, topk: int = 20) -> float:
        """计算两段文本的关键词 Jaccard 相似度"""
        kw_a = self.extract_keywords(text_a, topk)
        kw_b = self.extract_keywords(text_b, topk)
        if not kw_a or not kw_b:
            return 0.0
        intersection = kw_a & kw_b
        union = kw_a | kw_b
        return len(intersection) / len(union) if union else 0.0
