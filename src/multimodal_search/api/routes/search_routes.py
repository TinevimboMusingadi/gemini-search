"""
Search route: GET/POST query, returns hybrid search results.
"""
import logging

from fastapi import APIRouter, Depends, Query

from multimodal_search.api.dependencies import get_db, get_search_engine
from multimodal_search.core.schemas.search import SearchRequest, SearchResponse
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=SearchResponse)
def search_get(
    q: str = Query(..., min_length=1),
    top_k: int = Query(20, ge=1, le=100),
    search_fn=Depends(get_search_engine),
):
    """Hybrid search via query string."""
    req = SearchRequest(query=q, top_k=top_k)
    return search_fn(req)


@router.post("", response_model=SearchResponse)
def search_post(
    req: SearchRequest,
    search_fn=Depends(get_search_engine),
):
    """Hybrid search via JSON body."""
    return search_fn(req)
