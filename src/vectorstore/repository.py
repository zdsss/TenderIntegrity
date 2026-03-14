"""ChromaDB 仓库：CRUD 封装"""
import logging
from typing import Any

from src.document.metadata_extractor import ParagraphChunk
from src.vectorstore.client import get_chroma_client
from src.vectorstore.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

COLLECTION_CHUNKS = "tender_chunks"
COLLECTION_WHITELIST = "whitelist_phrases"


class ChromaRepository:
    """ChromaDB 操作封装，管理 tender_chunks 和 whitelist_phrases 两个集合"""

    def __init__(
        self,
        embedding_service: EmbeddingService,
        persist_dir: str = "./data/chromadb",
    ):
        self.embedding_service = embedding_service
        self.client = get_chroma_client(persist_dir)

    def _get_collection(self, name: str) -> Any:
        return self.client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"},
        )

    # ── 写入段落块 ──────────────────────────────────────────────
    def upsert_chunks(self, chunks: list[ParagraphChunk], task_id: str) -> None:
        """批量写入段落块到 ChromaDB"""
        if not chunks:
            return

        collection = self._get_collection(COLLECTION_CHUNKS)
        texts = [c.text for c in chunks]
        embeddings = self.embedding_service.embed_texts(texts)

        ids = [c.chunk_id for c in chunks]
        metadatas = [
            {
                "task_id": task_id,
                "doc_id": c.doc_id,
                "page_num": c.page_num,
                "section_title": c.section_title,
                "chunk_type": c.chunk_type,
                "is_whitelisted": str(c.is_whitelisted),
                "chunk_index": c.chunk_index,
            }
            for c in chunks
        ]

        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )
        logger.info(f"写入 {len(chunks)} 个段落块到 ChromaDB (task={task_id})")

    # ── 跨文档相似检索 ────────────────────────────────────────────
    def query_similar(
        self,
        query_chunk: ParagraphChunk,
        exclude_doc_id: str,
        task_id: str,
        top_k: int = 5,
        min_similarity: float = 0.70,
    ) -> list[dict]:
        """
        从 exclude_doc_id 以外的文档中检索与 query_chunk 最相似的段落

        Returns:
            list of {chunk_id, doc_id, text, similarity, metadata}
        """
        collection = self._get_collection(COLLECTION_CHUNKS)
        query_embedding = self.embedding_service.embed_single(query_chunk.text)

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k + 10,  # 多取一些再过滤
            where={
                "$and": [
                    {"task_id": {"$eq": task_id}},
                    {"doc_id": {"$ne": exclude_doc_id}},
                ]
            },
            include=["documents", "metadatas", "distances"],
        )

        hits = []
        if not results["ids"] or not results["ids"][0]:
            return hits

        for idx, (chunk_id, doc, meta, dist) in enumerate(
            zip(
                results["ids"][0],
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            )
        ):
            # ChromaDB cosine distance: similarity = 1 - distance
            similarity = 1.0 - float(dist)
            if similarity < min_similarity:
                continue
            if len(hits) >= top_k:
                break
            hits.append(
                {
                    "chunk_id": chunk_id,
                    "doc_id": meta.get("doc_id", ""),
                    "text": doc,
                    "similarity": similarity,
                    "metadata": meta,
                }
            )

        return hits

    # ── 白名单集合 ────────────────────────────────────────────────
    def upsert_whitelist_phrases(self, phrases: list[str]) -> None:
        """写入通用表述到白名单集合"""
        if not phrases:
            return
        collection = self._get_collection(COLLECTION_WHITELIST)
        embeddings = self.embedding_service.embed_texts(phrases)
        ids = [f"wl_{i:06d}" for i in range(len(phrases))]
        collection.upsert(ids=ids, embeddings=embeddings, documents=phrases)
        logger.info(f"写入 {len(phrases)} 条白名单表述")

    def is_whitelist_similar(self, text: str, threshold: float = 0.88) -> bool:
        """判断文本是否与白名单高度相似"""
        collection = self._get_collection(COLLECTION_WHITELIST)
        count = collection.count()
        if count == 0:
            return False

        embedding = self.embedding_service.embed_single(text)
        results = collection.query(
            query_embeddings=[embedding],
            n_results=1,
            include=["distances"],
        )
        if not results["distances"] or not results["distances"][0]:
            return False

        similarity = 1.0 - float(results["distances"][0][0])
        return similarity >= threshold

    # ── 清理 ─────────────────────────────────────────────────────
    def delete_task_chunks(self, task_id: str) -> None:
        """删除任务相关的所有段落块"""
        collection = self._get_collection(COLLECTION_CHUNKS)
        collection.delete(where={"task_id": {"$eq": task_id}})
        logger.info(f"已删除 task={task_id} 的向量数据")
