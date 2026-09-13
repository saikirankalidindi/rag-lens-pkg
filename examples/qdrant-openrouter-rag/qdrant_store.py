"""
Qdrant Vector Database Integration.

Connects to Qdrant Cloud when QDRANT_URL and QDRANT_API_KEY are configured,
otherwise gracefully falls back to local embedded Qdrant storage.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import NAMESPACE_URL, uuid5

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams

load_dotenv()

DEFAULT_COLLECTION = os.getenv("QDRANT_COLLECTION_NAME", "bookmyshow_rag")
VECTOR_DIMENSION = 1536  # text-embedding-3-small dimension


class QdrantStore:
    def __init__(
        self,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        collection_name: str = DEFAULT_COLLECTION,
    ):
        self.url = url if url is not None else os.getenv("QDRANT_URL", "").strip()
        self.api_key = api_key if api_key is not None else os.getenv("QDRANT_API_KEY", "").strip()
        self.collection_name = collection_name

        if self.url and self.api_key:
            # Connect to Qdrant Cloud cluster
            self.mode = "cloud"
            self.client = QdrantClient(url=self.url, api_key=self.api_key, timeout=30)
        else:
            # Fallback to embedded local on-disk storage
            self.mode = "local"
            storage_path = Path(__file__).resolve().parent / "qdrant_storage"
            storage_path.mkdir(parents=True, exist_ok=True)
            self.client = QdrantClient(path=str(storage_path))

    def ensure_collection(self, vector_size: int = VECTOR_DIMENSION):
        """Ensure collection exists in Qdrant with Cosine distance."""
        exists = self.client.collection_exists(self.collection_name)
        if not exists:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )

    def count(self) -> int:
        """Return total indexed points in collection."""
        if not self.client.collection_exists(self.collection_name):
            return 0
        return self.client.count(self.collection_name).count

    def index_documents(
        self,
        documents: List[Dict[str, Any]],
        embeddings: List[List[float]],
    ) -> int:
        """Upsert document chunks and their real vector embeddings into Qdrant."""
        self.ensure_collection()
        points = []
        for doc, vector in zip(documents, embeddings):
            # Deterministic UUID from document ID
            point_id = str(uuid5(NAMESPACE_URL, doc["id"]))
            points.append(
                models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "id": doc["id"],
                        "title": doc["title"],
                        "content": doc["content"],
                        "category": doc.get("category", "general"),
                    },
                )
            )

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
        )
        return len(points)

    def search(
        self,
        query_vector: List[float],
        top_k: int = 4,
        score_threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform real cosine vector search in Qdrant.
        Returns structured results compatible with RAGLens log_retrieval.
        """
        self.ensure_collection()
        res = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=top_k,
            score_threshold=score_threshold,
        )

        results = []
        for rank, pt in enumerate(res.points, 1):
            payload = pt.payload or {}
            score = round(float(pt.score), 4)
            results.append({
                "rank": rank,
                "chunk_id": f"{payload.get('id', rank)}_c1",
                "document_id": payload.get("id", str(rank)),
                "document_name": payload.get("title", "Unknown Document"),
                "content": payload.get("content", ""),
                "score": score,
                "retrieval_method": "qdrant_cosine",
                "selected": score >= 0.35,  # Chunks passed into LLM context
                "metadata": {
                    "category": payload.get("category", "general"),
                    "qdrant_mode": self.mode,
                },
            })
        return results
