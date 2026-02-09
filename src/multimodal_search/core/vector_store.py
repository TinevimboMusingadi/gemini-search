"""
Vector store abstraction: add(ids, vectors, metadata), search(vector, top_k).
Backends: in-memory (numpy) or ChromaDB (local persistent).
"""
import logging
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)

# Default collection name for ChromaDB
CHROMA_COLLECTION_NAME = "multimodal_embeddings"


def _sanitize_metadata_for_chroma(meta: Dict[str, Any]) -> Dict[str, str | int | float | bool]:
    """Chroma allows only str, int, float, bool. Omit None and convert values."""
    out = {}
    for k, v in meta.items():
        if v is None:
            continue
        if isinstance(v, (str, int, float, bool)):
            out[k] = v
        else:
            out[k] = str(v)
    return out


class VectorStoreInterface:
    """Interface for vector storage and similarity search."""

    def add(
        self,
        ids: List[str],
        vectors: List[List[float]],
        metadata: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Insert vectors with optional metadata. ids[i] and metadata[i] correspond to vectors[i]."""
        raise NotImplementedError

    def search(
        self,
        vector: List[float],
        top_k: int = 20,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[tuple[str, float, Dict[str, Any]]]:
        """Return list of (id, score, metadata) sorted by score descending."""
        raise NotImplementedError


class InMemoryVectorStore(VectorStoreInterface):
    """In-memory store using numpy for dot-product similarity (vectors assumed normalized for cosine)."""

    def __init__(self, dimension: int = 1408) -> None:
        self.dimension = dimension
        self._ids: List[str] = []
        self._vectors: Optional[np.ndarray] = None
        self._metadata: List[Dict[str, Any]] = []
        logger.info("InMemoryVectorStore initialized with dimension=%s", dimension)

    def add(
        self,
        ids: List[str],
        vectors: List[List[float]],
        metadata: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        if not ids or not vectors:
            logger.warning("VectorStore.add called with empty ids or vectors")
            return
        if len(ids) != len(vectors):
            raise ValueError("ids and vectors length mismatch")
        meta = metadata or [{}] * len(ids)
        if len(meta) != len(ids):
            meta = [{}] * len(ids)
        arr = np.array(vectors, dtype=np.float32)
        if arr.shape[1] != self.dimension:
            raise ValueError(f"Vector dimension {arr.shape[1]} != {self.dimension}")
        self._ids.extend(ids)
        self._metadata.extend(meta)
        if self._vectors is None:
            self._vectors = arr
        else:
            self._vectors = np.vstack([self._vectors, arr])
        logger.debug("VectorStore: added %s vectors; total=%s", len(ids), len(self._ids))

    def search(
        self,
        vector: List[float],
        top_k: int = 20,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[tuple[str, float, Dict[str, Any]]]:
        if self._vectors is None or len(self._ids) == 0:
            logger.debug("VectorStore: empty store, returning []")
            return []
        q = np.array([vector], dtype=np.float32)
        scores = np.dot(self._vectors, q.T).flatten()
        indices = np.argsort(scores)[::-1][:top_k]
        out = []
        for i in indices:
            if filter_metadata:
                meta = self._metadata[i]
                if not all(meta.get(k) == v for k, v in filter_metadata.items()):
                    continue
            out.append((self._ids[i], float(scores[i]), self._metadata[i]))
        return out[:top_k]


class ChromaVectorStore(VectorStoreInterface):
    """ChromaDB-backed persistent vector store (local). Uses cosine similarity."""

    def __init__(
        self,
        persist_directory: str | None = None,
        collection_name: str = CHROMA_COLLECTION_NAME,
        dimension: int = 1408,
    ) -> None:
        import chromadb
        from chromadb.config import Settings as ChromaSettings

        self.dimension = dimension
        self._collection_name = collection_name
        path = str(persist_directory) if persist_directory else None
        if path:
            self._client = chromadb.PersistentClient(
                path=path,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            logger.info("ChromaVectorStore: persistent path=%s", path)
        else:
            self._client = chromadb.Client(settings=ChromaSettings(anonymized_telemetry=False))
            logger.info("ChromaVectorStore: ephemeral (in-memory)")
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("ChromaVectorStore initialized (collection=%s, dim=%s)", collection_name, dimension)

    def add(
        self,
        ids: List[str],
        vectors: List[List[float]],
        metadata: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        if not ids or not vectors:
            logger.warning("VectorStore.add called with empty ids or vectors")
            return
        if len(ids) != len(vectors):
            raise ValueError("ids and vectors length mismatch")
        meta = metadata or [{}] * len(ids)
        if len(meta) != len(ids):
            meta = [{}] * len(ids)
        metadatas = [_sanitize_metadata_for_chroma(m) for m in meta]
        self._collection.add(ids=ids, embeddings=vectors, metadatas=metadatas)
        logger.debug("ChromaVectorStore: added %s vectors", len(ids))

    def search(
        self,
        vector: List[float],
        top_k: int = 20,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[tuple[str, float, Dict[str, Any]]]:
        where = None
        if filter_metadata:
            where = {k: v for k, v in filter_metadata.items() if v is not None}
            where = _sanitize_metadata_for_chroma(where) if where else None
        result = self._collection.query(
            query_embeddings=[vector],
            n_results=top_k,
            where=where,
            include=["metadatas", "distances"],
        )
        # Chroma cosine distance: 0 = identical, 2 = opposite. Similarity = 1 - distance.
        ids = result["ids"][0] if result["ids"] else []
        distances = result["distances"][0] if result["distances"] else []
        metadatas = result["metadatas"][0] if result["metadatas"] else []
        out = []
        for i, vid in enumerate(ids):
            dist = distances[i] if i < len(distances) else 0.0
            meta = metadatas[i] if i < len(metadatas) else {}
            score = 1.0 - min(1.0, float(dist)) if dist is not None else 0.0
            out.append((vid, score, meta))
        return out


_vector_store: Optional[VectorStoreInterface] = None


def get_vector_store(dimension: Optional[int] = None) -> VectorStoreInterface:
    """Return singleton vector store. Backend from config: 'memory' or 'chroma'."""
    global _vector_store
    if _vector_store is None:
        from multimodal_search.core.config import get_settings
        settings = get_settings()
        dim = dimension or settings.embedding_dimension
        backend = (settings.vector_store_backend or "memory").strip().lower()
        if backend == "chroma":
            try:
                persist_dir = settings.resolved_chroma_dir
                persist_dir.mkdir(parents=True, exist_ok=True)
                _vector_store = ChromaVectorStore(
                    persist_directory=str(persist_dir),
                    collection_name=CHROMA_COLLECTION_NAME,
                    dimension=dim,
                )
                logger.info("Vector store singleton initialized (ChromaVectorStore, dir=%s)", persist_dir)
            except Exception as e:
                logger.error("Failed to initialize ChromaDB (Python 3.14 compatibility?): %s", e)
                logger.warning("Falling back to InMemoryVectorStore (Search will be empty/ephemeral!)")
                _vector_store = InMemoryVectorStore(dimension=dim)
        else:
            _vector_store = InMemoryVectorStore(dimension=dim)
            logger.info("Vector store singleton initialized (InMemoryVectorStore, dim=%s)", dim)
    return _vector_store
