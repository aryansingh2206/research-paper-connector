"""
Embedding generation using sentence-transformers
Offline-safe, snapshot-pinned, Docker-safe.
"""

import logging
from typing import List, Union
import numpy as np
import os
from pathlib import Path

from sentence_transformers import SentenceTransformer
from src.config import settings

logger = logging.getLogger(__name__)


class EmbeddingModel:
    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL

        # Enforce offline mode
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
        os.environ.setdefault("HF_HUB_OFFLINE", "1")

        hf_home = Path(os.environ.get("HF_HOME", "/root/.cache/huggingface"))

        snapshot_path = (
            hf_home
            / "hub"
            / "models--sentence-transformers--all-MiniLM-L6-v2"
            / "snapshots"
            / "c9745ed1d9f207416be6d2e6f8de32d1f16199bf"
        )

        logger.info(f"Loading embedding model from snapshot: {snapshot_path}")

        if not snapshot_path.exists():
            raise RuntimeError(f"Snapshot path not found: {snapshot_path}")

        try:
            self.model = SentenceTransformer(
                str(snapshot_path),
                device="cpu"
            )
            self.dimension = self.model.get_sentence_embedding_dimension()
            logger.info(f"Embedding model loaded (dim={self.dimension})")

        except Exception as e:
            logger.exception("Failed to load embedding model")
            raise RuntimeError(f"Embedding model load failed: {e}") from e

    def embed_text(self, text: str) -> List[float]:
        return self.model.encode(text, convert_to_numpy=True).tolist()

    def embed_batch(
        self,
        texts: List[str],
        batch_size: int | None = None,
        show_progress: bool = True
    ) -> List[List[float]]:
        if not texts:
            return []

        batch_size = batch_size or settings.EMBEDDING_BATCH_SIZE
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True
        )
        return embeddings.tolist()

    def compute_similarity(
        self,
        embedding1: Union[List[float], np.ndarray],
        embedding2: Union[List[float], np.ndarray]
    ) -> float:
        v1 = np.asarray(embedding1)
        v2 = np.asarray(embedding2)
        denom = np.linalg.norm(v1) * np.linalg.norm(v2)
        return float(np.dot(v1, v2) / denom) if denom else 0.0


_embedding_model: EmbeddingModel | None = None


def get_embedding_model() -> EmbeddingModel:
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = EmbeddingModel()
    return _embedding_model
