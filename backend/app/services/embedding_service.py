"""
Embedding Service — Multilingual Sentence Transformers
Encodes FIR text into dense vectors for semantic similarity search.
Uses: paraphrase-multilingual-MiniLM-L12-v2 (supports English + Malayalam)
"""

import logging
import os
from typing import List, Optional

import numpy as np

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Singleton sentence-transformer encoder.
    Supports English and Malayalam text directly (multilingual model).
    """

    def __init__(self):
        self._model = None
        self._model_name = settings.EMBEDDING_MODEL
        self._cache_dir = settings.MODEL_CACHE_DIR

    def _load_model(self):
        if self._model is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer
            os.makedirs(self._cache_dir, exist_ok=True)
            logger.info(f"Loading embedding model: {self._model_name}")
            self._model = SentenceTransformer(
                self._model_name,
                cache_folder=self._cache_dir,
            )
            logger.info("✅ Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load embedding model: {e}")
            self._model = None

    def warmup(self):
        """Pre-load model during application startup."""
        self._load_model()
        if self._model:
            # Encode a dummy sentence to compile any lazy operations
            self._model.encode("warmup", convert_to_numpy=True)
            logger.info("✅ Embedding model warmed up")

    def embed(self, text: str) -> Optional[List[float]]:
        """
        Encode text into a 384-dimensional vector.
        Returns None if model unavailable (fallback: caller skips ChromaDB indexing).
        """
        self._load_model()
        if self._model is None:
            logger.warning("Embedding model not available — returning None")
            return None
        try:
            # Truncate very long text to first 512 tokens (model limit)
            text = text[:5000]
            vector = self._model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
            return vector.tolist()
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            return None

    def embed_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Batch encoding for efficiency."""
        self._load_model()
        if self._model is None:
            return [None] * len(texts)
        try:
            texts = [t[:5000] for t in texts]
            vectors = self._model.encode(texts, convert_to_numpy=True, normalize_embeddings=True, batch_size=16, show_progress_bar=True)
            return [v.tolist() for v in vectors]
        except Exception as e:
            logger.error(f"Batch embedding error: {e}")
            return [None] * len(texts)

    def cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        a, b = np.array(v1), np.array(v2)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


_embedding_service_instance: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    global _embedding_service_instance
    if _embedding_service_instance is None:
        _embedding_service_instance = EmbeddingService()
    return _embedding_service_instance
