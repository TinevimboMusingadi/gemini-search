"""
Reciprocal Rank Fusion (RRF) to merge keyword and vector result lists.
RRF score = sum 1 / (k + rank_i); default k=60.
"""
import logging
from typing import List, Tuple, Any

logger = logging.getLogger(__name__)

DEFAULT_K = 60


def rrf_merge(
    result_lists: List[List[Tuple[str, float, Any]]],
    k: int = DEFAULT_K,
) -> List[Tuple[str, float]]:
    """
    Merge multiple ranked lists by RRF. Each list is [(id, score, ...), ...].
    Returns list of (id, rrf_score) sorted by rrf_score descending.
    """
    rrf_scores = {}
    for lst in result_lists:
        for rank, item in enumerate(lst):
            id_ = item[0]
            rrf_scores[id_] = rrf_scores.get(id_, 0) + 1.0 / (k + rank + 1)
    out = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    logger.debug("RRF merged %s lists -> %s unique ids", len(result_lists), len(out))
    return out
