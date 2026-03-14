#!/usr/bin/env python3
"""初始化白名单数据到 ChromaDB"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def load_common_phrases(filepath: Path) -> list[str]:
    """加载通用表述列表"""
    if not filepath.exists():
        logger.warning(f"文件不存在: {filepath}")
        return []
    phrases = []
    for line in filepath.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            phrases.append(line)
    return phrases


def main():
    from config.settings import settings
    from src.vectorstore.embedding_service import EmbeddingService
    from src.vectorstore.repository import ChromaRepository

    phrases_file = settings.whitelist_dir / "common_phrases.txt"
    phrases = load_common_phrases(phrases_file)

    if not phrases:
        logger.warning("未找到白名单表述，请检查 config/whitelist/common_phrases.txt")
        return

    logger.info(f"加载 {len(phrases)} 条通用表述")

    embedding_service = EmbeddingService(
        model_name=settings.embedding_model,
        device=settings.embedding_device,
    )
    repo = ChromaRepository(embedding_service, persist_dir=settings.chroma_persist_dir)
    repo.upsert_whitelist_phrases(phrases)

    logger.info("白名单初始化完成！")
    print(f"\n✅ 已成功写入 {len(phrases)} 条白名单表述到 ChromaDB")
    print(f"   ChromaDB 路径: {settings.chroma_persist_dir}")


if __name__ == "__main__":
    main()
