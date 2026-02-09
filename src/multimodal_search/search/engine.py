"""
Search coordinator: keyword-only, semantic-only, or hybrid (keyword + vector, RRF merge).
"""
import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from multimodal_search.core.schemas.search import SearchRequest, SearchResponse, SearchResultItem
from multimodal_search.core.database import TextChunk, Region, Document, Page
from multimodal_search.search.keyword_search import keyword_search
from multimodal_search.search.rankers.rrf import rrf_merge
from multimodal_search.search.retrievers.vector_retriever import vector_search

logger = logging.getLogger(__name__)


def _row_to_item(
    doc_id: int,
    title: str,
    page_id: int,
    page_num: int,
    result_type: str,
    chunk_id: Optional[int],
    region_id: Optional[int],
    snippet: str,
    score: float,
    vector_id: Optional[str],
) -> SearchResultItem:
    """Build SearchResultItem from resolved fields."""
    return SearchResultItem(
        document_id=doc_id,
        document_title=title,
        page_id=page_id,
        page_num=page_num,
        result_type=result_type,
        chunk_id=chunk_id,
        region_id=region_id,
        snippet=snippet,
        score=round(score, 4),
        vector_id=vector_id,
    )


def _resolve_vector_ids(
    session: Session,
    vector_ids: List[str],
) -> dict:
    """Resolve vector_id -> (doc_id, title, page_id, page_num, type, chunk_id, region_id, snippet)."""
    if not vector_ids:
        return {}

    id_to_info = {}
    
    # 1. Batch query TextChunks with joins
    # We need: doc.filename, page.page_num
    chunks = (
        session.query(TextChunk, Document, Page)
        .join(Document, TextChunk.document_id == Document.id)
        .join(Page, TextChunk.page_id == Page.id)
        .filter(TextChunk.vector_id.in_(vector_ids))
        .all()
    )
    
    for tc, doc, page in chunks:
        id_to_info[tc.vector_id] = (
            tc.document_id,
            doc.filename,
            tc.page_id,
            page.page_num,
            "text",
            tc.id,
            None,
            (tc.text or "")[:500],
        )

    # 2. Batch query Regions with joins
    # Only query for vector_ids we haven't found yet (though they shouldn't overlap)
    remaining_ids = [vid for vid in vector_ids if vid not in id_to_info]
    if remaining_ids:
        regions = (
            session.query(Region, Document, Page)
            .join(Document, Region.document_id == Document.id)
            .join(Page, Region.page_id == Page.id)
            .filter(Region.vector_id.in_(remaining_ids))
            .all()
        )
        for reg, doc, page in regions:
            id_to_info[reg.vector_id] = (
                reg.document_id,
                doc.filename,
                reg.page_id,
                page.page_num,
                "image",
                None,
                reg.id,
                reg.label or "",
            )
            
    return id_to_info


def search(
    session: Session,
    request: SearchRequest,
) -> SearchResponse:
    """
    Run search by mode: keyword only, semantic only, or hybrid (keyword + vector, RRF).
    """
    query = request.query.strip()
    top_k = request.top_k
    mode = request.mode or "hybrid"
    if not query:
        logger.warning("Empty search query")
        return SearchResponse(query=request.query, results=[])

    if mode == "keyword":
        kw_results = keyword_search(session, query, top_k=top_k)
        results = [
            _row_to_item(
                r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9]
            )
            for r in kw_results
        ]
        logger.info("Keyword search returned %s results for query=%s", len(results), query[:50])
        return SearchResponse(query=request.query, results=results)

    if mode == "semantic":
        vec_results = vector_search(query, top_k=top_k)
        if not vec_results:
            return SearchResponse(query=request.query, results=[])
        vector_ids = [vid for vid, _, _ in vec_results]
        id_to_info = _resolve_vector_ids(session, vector_ids)
        results = []
        for vid, score, _ in vec_results:
            info = id_to_info.get(vid)
            if not info:
                continue
            doc_id, title, page_id, page_num, typ, chunk_id, region_id, snippet = info
            results.append(
                _row_to_item(
                    doc_id, title, page_id, page_num, typ,
                    chunk_id, region_id, snippet, score, vid,
                )
            )
        logger.info("Semantic search returned %s results for query=%s", len(results), query[:50])
        return SearchResponse(query=request.query, results=results)

    # hybrid: keyword + vector, RRF merge
    kw_results = keyword_search(session, query, top_k=top_k)
    vec_results = vector_search(query, top_k=top_k)
    kw_list = [(r[9], r[8]) for r in kw_results if r[9]]
    vec_list = [(vid, sc) for vid, sc, _ in vec_results]
    if not kw_list and not vec_list:
        logger.debug("No keyword or vector results")
        return SearchResponse(query=request.query, results=[])

    merged = rrf_merge([kw_list, vec_list])
    vector_ids = [m[0] for m in merged[:top_k]]
    id_to_info = {}
    for r in kw_results:
        if r[9]:
            id_to_info[r[9]] = (r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7])
    for vid in vector_ids:
        if vid in id_to_info:
            continue
        id_to_info.update(_resolve_vector_ids(session, [vid]))

    results = []
    for vid, rrf_score in merged[:top_k]:
        info = id_to_info.get(vid)
        if not info:
            continue
        doc_id, title, page_id, page_num, typ, chunk_id, region_id, snippet = info
        results.append(
            _row_to_item(
                doc_id, title, page_id, page_num, typ,
                chunk_id, region_id, snippet, rrf_score, vid,
            )
        )
    logger.info("Hybrid search returned %s results for query=%s", len(results), query[:50])
    return SearchResponse(query=request.query, results=results)
