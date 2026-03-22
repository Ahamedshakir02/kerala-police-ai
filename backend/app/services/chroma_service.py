"""
ChromaDB Service — Vector Store for Semantic FIR Similarity Search
Stores FIR embeddings and retrieves top-K similar cases.
"""

import logging
from typing import List, Dict, Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

COLLECTION_NAME = "fir_embeddings"


class ChromaService:
    def __init__(self):
        self._client = None
        self._collection = None
        self._connect()

    def _connect(self):
        try:
            import chromadb
            self._client = chromadb.HttpClient(
                host=settings.CHROMA_HOST,
                port=settings.CHROMA_PORT,
            )
            self._client.heartbeat()
            self._collection = self._client.get_or_create_collection(
                name=COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(f"✅ ChromaDB connected — collection '{COLLECTION_NAME}' ready (docs: {self._collection.count()})")
        except Exception as e:
            logger.warning(f"⚠️ ChromaDB not available: {e}. Similarity search will be disabled.")
            self._client = None
            self._collection = None

    @property
    def is_available(self) -> bool:
        return self._collection is not None

    def upsert_fir(self, fir_id: str, vector: List[float], metadata: Dict[str, Any]) -> bool:
        """Index a FIR into ChromaDB with its embedding vector and metadata."""
        if not self.is_available:
            return False
        try:
            self._collection.upsert(
                ids=[fir_id],
                embeddings=[vector],
                metadatas=[{k: str(v) if v is not None else "" for k, v in metadata.items()}],
            )
            return True
        except Exception as e:
            logger.error(f"ChromaDB upsert error: {e}")
            return False

    def search_similar(
        self,
        vector: List[float],
        k: int = 5,
        exclude_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Find top-K semantically similar FIRs.
        Returns list of {id, distance, metadata}.
        """
        if not self.is_available or self._collection.count() == 0:
            return []
        try:
            # ChromaDB returns distance (lower = more similar for cosine)
            results = self._collection.query(
                query_embeddings=[vector],
                n_results=min(k + (len(exclude_ids or [])), max(self._collection.count(), 1)),
                include=["metadatas", "distances"],
            )
            hits = []
            ids = results["ids"][0]
            metas = results["metadatas"][0]
            dists = results["distances"][0]

            for rid, meta, dist in zip(ids, metas, dists):
                if exclude_ids and rid in exclude_ids:
                    continue
                similarity = round(1.0 - dist, 4)  # cosine distance → similarity
                hits.append({"id": rid, "similarity": similarity, "metadata": meta})

            return hits[:k]
        except Exception as e:
            logger.error(f"ChromaDB search error: {e}")
            return []

    def delete_fir(self, fir_id: str) -> bool:
        if not self.is_available:
            return False
        try:
            self._collection.delete(ids=[fir_id])
            return True
        except Exception as e:
            logger.error(f"ChromaDB delete error: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        if not self.is_available:
            return {"available": False, "count": 0}
        return {"available": True, "count": self._collection.count()}


_chroma_instance: Optional[ChromaService] = None


def get_chroma_service() -> ChromaService:
    global _chroma_instance
    if _chroma_instance is None:
        _chroma_instance = ChromaService()
    return _chroma_instance
