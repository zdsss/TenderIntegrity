"""ChromaDB 客户端单例"""
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_client_instance: Any = None


def get_chroma_client(persist_dir: str = "./data/chromadb") -> Any:
    """获取 ChromaDB 持久化客户端（单例）"""
    global _client_instance
    if _client_instance is None:
        try:
            import chromadb
        except ImportError:
            raise ImportError("请安装 chromadb: uv add chromadb")

        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        _client_instance = chromadb.PersistentClient(path=persist_dir)
        logger.info(f"ChromaDB 客户端初始化完成: {persist_dir}")
    return _client_instance


def reset_client():
    """重置客户端（测试用）"""
    global _client_instance
    _client_instance = None
