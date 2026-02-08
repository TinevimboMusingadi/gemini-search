"""
Vector (semantic) search: embed query, search vector store, return (id, score, metadata).
"""
import logging
from typing import List, Tuple, Any, Dict

from multimodal_search.core.vector_store import get_vector_store
from multimodal_search.services.vertex_embedder import embed_query

logger = logging.getLogger(__name__)


def vector_search(
    query: str,
    top_k: int = 20,
) -> List[Tuple[str, float, Dict[str, Any]]]:
    """
    Embed query and search vector store. Returns list of (vector_id, score, metadata).
    """
    try:
        qvec = embed_query(query)
    except Exception as e:
        logger.exception("Vector embed_query failed: %s", e)
        return []
    store = get_vector_store()
    hits = store.search(qvec, top_k=top_k)
    logger.debug("Vector search returned %s hits", len(hits))
    return hits
