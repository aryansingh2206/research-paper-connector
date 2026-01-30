"""
Endee Vector Database HTTP Client
Correct for Endee OSS (Docker server)
"""

import httpx
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from src.config import settings

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Data models
# ------------------------------------------------------------------
@dataclass
class VectorDocument:
    id: str
    vector: List[float]
    metadata: Dict[str, Any]


@dataclass
class SearchResult:
    id: str
    score: float
    metadata: Dict[str, Any]


# ------------------------------------------------------------------
# Client
# ------------------------------------------------------------------
class EndeeClient:
    def __init__(
        self,
        base_url: Optional[str] = None,
        collection: Optional[str] = None,
        timeout: float = 30.0
    ):
        self.base_url = base_url or settings.endee_base_url
        self.collection = collection or settings.ENDEE_COLLECTION

        self.client = httpx.Client(
            timeout=timeout,
            headers={"Content-Type": "application/json"}
        )

        logger.info(f"Initialized Endee client: {self.base_url}")

    def __del__(self):
        try:
            self.client.close()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------
    def health_check(self) -> bool:
        try:
            r = self.client.get(f"{self.base_url}/api/v1/health")
            return r.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    # ------------------------------------------------------------------
    # Collection handling (implicit)
    # ------------------------------------------------------------------
    def create_collection(self, *_, **__) -> bool:
        return True

    def delete_collection(self) -> bool:
        try:
            r = self.client.delete(
                f"{self.base_url}/api/v1/index/{self.collection}"
            )
            return r.status_code in (200, 204, 404)
        except Exception as e:
            logger.error(f"Delete index failed: {e}")
            return False

    # ------------------------------------------------------------------
    # INSERT VECTORS ✅ FINAL & CORRECT
    # ------------------------------------------------------------------
    def insert_vectors(
        self,
        documents: List[VectorDocument],
        batch_size: int = 100
    ) -> bool:
        """
        Endee OSS requires:
        PUT /api/v1/points
        """
        try:
            url = f"{self.base_url}/api/v1/points"

            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]

                payload = {
                    "index": self.collection,
                    "points": [
                        {
                            "id": doc.id,
                            "vector": doc.vector,
                            "metadata": doc.metadata
                        }
                        for doc in batch
                    ]
                }

                response = self.client.put(url, json=payload)

                if response.status_code not in (200, 201):
                    logger.error(
                        f"Insert failed [{response.status_code}]: {response.text}"
                    )
                    return False

            logger.info(f"Successfully inserted {len(documents)} vectors")
            return True

        except Exception as e:
            logger.exception(f"Vector insert error: {e}")
            return False

    # ------------------------------------------------------------------
    # SEARCH
    # ------------------------------------------------------------------
    def search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        try:
            url = f"{self.base_url}/api/v1/search"

            payload = {
                "index": self.collection,
                "vector": query_vector,
                "k": top_k
            }

            if filter_metadata:
                payload["filter"] = filter_metadata

            response = self.client.post(url, json=payload)

            if response.status_code != 200:
                logger.error(f"Search failed: {response.text}")
                return []

            data = response.json()

            return [
                SearchResult(
                    id=item["id"],
                    score=item["score"],
                    metadata=item.get("metadata", {})
                )
                for item in data.get("results", [])
            ]

        except Exception as e:
            logger.exception(f"Search error: {e}")
            return []
