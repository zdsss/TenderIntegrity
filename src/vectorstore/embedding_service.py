"""Embedding 服务：支持本地 BGE-M3 和远程 API（阿里云百炼等 OpenAI 兼容接口）"""
import logging
from typing import Any

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    向量化服务，支持两种模式：
    - 本地模式：sentence-transformers（BGE-M3 等）
    - API 模式：OpenAI 兼容接口（阿里云百炼 qwen3-vl-embedding 等）
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-m3",
        device: str = "cpu",
        batch_size: int = 32,
        use_api: bool = False,
        api_key: str | None = None,
        api_base_url: str | None = None,
    ):
        self.model_name = model_name
        self.device = device
        self.batch_size = batch_size
        self.use_api = use_api
        self.api_key = api_key
        self.api_base_url = api_base_url
        self._model: Any = None
        self._api_client: Any = None

    def _load_model(self):
        """加载本地模型（懒加载）"""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"加载 Embedding 模型: {self.model_name} (device={self.device})")
                self._model = SentenceTransformer(self.model_name, device=self.device)
                logger.info("Embedding 模型加载完成")
            except ImportError:
                raise ImportError("请安装 sentence-transformers: uv add sentence-transformers")

    def _get_api_client(self):
        """获取 OpenAI 兼容客户端（懒加载）"""
        if self._api_client is None:
            try:
                from openai import OpenAI
                kwargs: dict = {}
                if self.api_key:
                    kwargs["api_key"] = self.api_key
                if self.api_base_url:
                    kwargs["base_url"] = self.api_base_url
                self._api_client = OpenAI(**kwargs)
                logger.info(f"API Embedding 客户端初始化: {self.model_name} @ {self.api_base_url}")
            except ImportError:
                raise ImportError("请安装 openai: uv add openai")
        return self._api_client

    def _embed_via_api(self, texts: list[str]) -> list[list[float]]:
        """通过 API 批量向量化"""
        client = self._get_api_client()
        all_embeddings: list[list[float]] = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i: i + self.batch_size]
            response = client.embeddings.create(
                model=self.model_name,
                input=batch,
            )
            batch_embeddings = [item.embedding for item in sorted(response.data, key=lambda x: x.index)]
            all_embeddings.extend(batch_embeddings)
            logger.debug(f"API 向量化进度: {min(i + self.batch_size, len(texts))}/{len(texts)}")
        return all_embeddings

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """批量向量化文本列表"""
        if not texts:
            return []

        if self.use_api:
            return self._embed_via_api(texts)

        self._load_model()
        all_embeddings: list[list[float]] = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i: i + self.batch_size]
            embeddings = self._model.encode(
                batch,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            all_embeddings.extend(embeddings.tolist())
            logger.debug(f"向量化进度: {min(i + self.batch_size, len(texts))}/{len(texts)}")
        return all_embeddings

    def embed_single(self, text: str) -> list[float]:
        """向量化单个文本"""
        return self.embed_texts([text])[0]

    @property
    def dimension(self) -> int:
        """返回向量维度"""
        if self.use_api:
            # 通过实际调用获取维度
            sample = self.embed_single("test")
            return len(sample)
        self._load_model()
        return self._model.get_sentence_embedding_dimension()
