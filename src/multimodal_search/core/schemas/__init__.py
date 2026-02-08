"""Pydantic schemas for request/response and domain models."""

from multimodal_search.core.schemas.document import (
    DocumentCreate,
    DocumentMetadata,
    PageMetadata,
)
from multimodal_search.core.schemas.search import (
    SearchRequest,
    SearchResponse,
    SearchResultItem,
)
from multimodal_search.core.schemas.vision import (
    BoundingBox,
    DetectedRegion,
)

__all__ = [
    "BoundingBox",
    "DetectedRegion",
    "DocumentCreate",
    "DocumentMetadata",
    "PageMetadata",
    "SearchRequest",
    "SearchResponse",
    "SearchResultItem",
]
