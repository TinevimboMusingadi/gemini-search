"""Pydantic models for search request/response and result items."""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

SearchMode = Literal["hybrid", "keyword", "semantic"]


class SearchRequest(BaseModel):
    """Search request; mode selects keyword-only, semantic-only, or hybrid."""

    query: str = Field(..., min_length=1, description="Search query")
    top_k: int = Field(default=20, ge=1, le=100, description="Max results to return")
    mode: SearchMode = Field(
        default="hybrid",
        description="hybrid = keyword + semantic (RRF); keyword = FTS only; semantic = vector only",
    )


class SearchResultItem(BaseModel):
    """Single result from hybrid search (keyword or semantic)."""

    document_id: int
    document_title: str
    page_id: int
    page_num: int
    result_type: str = Field(..., description="'text' or 'image' (region)")
    chunk_id: Optional[int] = None
    region_id: Optional[int] = None
    snippet: str = Field(..., description="Text snippet or region label")
    score: float = Field(default=0.0, description="Relevance score")
    vector_id: Optional[str] = None


class SearchResponse(BaseModel):
    """Response for hybrid search."""

    query: str
    results: List[SearchResultItem] = Field(default_factory=list)
