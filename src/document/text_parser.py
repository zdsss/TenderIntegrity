"""纯文本文档解析"""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class TextParser:
    """解析纯文本文件，自动检测编码"""

    def parse(self, file_path: str | Path) -> tuple[str, dict[int, int]]:
        """
        解析文本文件

        Returns:
            (full_text, page_map)  — 纯文本无页码信息，page_map 为空
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 自动检测编码
        raw = file_path.read_bytes()
        encoding = self._detect_encoding(raw)

        try:
            text = raw.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            text = raw.decode("utf-8", errors="replace")

        logger.info(f"TXT 解析完成: {file_path.name}, 编码={encoding}, {len(text)} 字符")
        return text, {}

    def _detect_encoding(self, raw: bytes) -> str:
        """检测字节串编码"""
        try:
            import chardet
            result = chardet.detect(raw)
            encoding = result.get("encoding") or "utf-8"
            # 统一 GBK 变体
            if encoding.lower() in ("gb2312", "gbk", "gb18030"):
                return "gb18030"
            return encoding
        except ImportError:
            return "utf-8"
