"""误报过滤：白名单三层防御"""
import logging
import re
from pathlib import Path

from src.document.metadata_extractor import ParagraphChunk

logger = logging.getLogger(__name__)


def _load_patterns(filepath: Path) -> list[re.Pattern]:
    """从文件加载正则模式（跳过注释行和空行）"""
    patterns = []
    if not filepath.exists():
        return patterns
    for line in filepath.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            patterns.append(re.compile(line))
        except re.error as e:
            logger.warning(f"无效正则: {line!r} — {e}")
    return patterns


class WhitelistFilter:
    """
    三层误报过滤：
    第1层（正则）：法规条文、标准引用
    第2层（向量）：通用行业表述（需 ChromaRepository）
    第3层（LLM）：由 LLM 节点在分析时主动识别（此处不处理）
    """

    def __init__(
        self,
        whitelist_dir: str | Path | None = None,
        chroma_repo=None,  # ChromaRepository | None
        whitelist_threshold: float = 0.88,
    ):
        if whitelist_dir is None:
            whitelist_dir = Path(__file__).parent.parent.parent / "config" / "whitelist"
        self.whitelist_dir = Path(whitelist_dir)
        self.chroma_repo = chroma_repo
        self.whitelist_threshold = whitelist_threshold

        # 加载正则模式
        self._legal_patterns = _load_patterns(self.whitelist_dir / "legal_refs.txt")
        self._standard_patterns = _load_patterns(self.whitelist_dir / "standard_refs.txt")

        logger.info(
            f"白名单过滤器加载: {len(self._legal_patterns)} 条法规规则, "
            f"{len(self._standard_patterns)} 条标准规则"
        )

    def is_whitelisted_regex(self, text: str) -> bool:
        """第1层：正则匹配白名单"""
        for pattern in self._legal_patterns:
            if pattern.search(text):
                return True
        for pattern in self._standard_patterns:
            if pattern.search(text):
                return True
        return False

    def is_whitelisted_vector(self, text: str) -> bool:
        """第2层：向量相似度白名单"""
        if self.chroma_repo is None:
            return False
        return self.chroma_repo.is_whitelist_similar(text, self.whitelist_threshold)

    def filter_chunks(self, chunks: list[ParagraphChunk]) -> list[ParagraphChunk]:
        """
        标记段落块的白名单状态（is_whitelisted=True）
        不移除段落块，仅标记，让后续评分使用惩罚系数
        """
        marked = 0
        for chunk in chunks:
            if self.is_whitelisted_regex(chunk.text):
                chunk.is_whitelisted = True
                marked += 1
            elif self.is_whitelisted_vector(chunk.text):
                chunk.is_whitelisted = True
                marked += 1

        logger.info(f"白名单过滤: {marked}/{len(chunks)} 个段落被标记为白名单")
        return chunks
