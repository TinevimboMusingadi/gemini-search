"""
Search coordinator: hybrid keyword + vector, RRF merge, return unified SearchResponse.
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


def search(
    session: Session,
    request: SearchRequest,
) -> SearchResponse:
    """
    Run hybrid search: keyword + vector, RRF merge, resolve to SearchResultItem list.
    """
    query = request.query.strip()
    top_k = request.top_k
    if not query:
        logger.warning("Empty search query")
        return SearchResponse(query=request.query, results=[])

    # Keyword results: (doc_id, title, page_id, page_num, type, chunk_id, region_id, snippet, score, vector_id)
    kw_results = keyword_search(session, query, top_k=top_k)
    # Vector results: (vector_id, score, metadata)
    vec_results = vector_search(query, top_k=top_k)

    # Build lists for RRF: (vector_id, score). Use vector_id as common key.
    kw_list = [(r[9], r[8]) for r in kw_results if r[9]]
    vec_list = [(vid, sc) for vid, sc, _ in vec_results]
    if not kw_list and not vec_list:
        logger.debug("No keyword or vector results")
        return SearchResponse(query=request.query, results=[])

    # RRF merge
    merged = rrf_merge([kw_list, vec_list])  # list of (vector_id, rrf_score)
    vector_ids = [m[0] for m in merged[:top_k]]

    # Resolve vector_id -> (document_id, title, page_id, page_num, type, chunk_id, region_id, snippet)
    id_to_info = {}
    for r in kw_results:
        if r[9]:
            id_to_info[r[9]] = (r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7])
    for vid in vector_ids:
        if vid in id_to_info:
            continue
        # Resolve by vector_id from DB
        tc = session.query(TextChunk).filter(TextChunk.vector_id == vid).first()
        if tc:
            doc = session.query(Document).filter(Document.id == tc.document_id).first()
            page = session.query(Page).filter(Page.id == tc.page_id).first()
            id_to_info[vid] = (
                tc.document_id,
                doc.filename if doc else "",
                tc.page_id,
                page.page_num if page else 0,
                "text",
                tc.id,
                None,
                (tc.text or "")[:500],
            )
            continue
        reg = session.query(Region).filter(Region.vector_id == vid).first()
        if reg:
            doc = session.query(Document).filter(Document.id == reg.document_id).first()
            page = session.query(Page).filter(Page.id == reg.page_id).first()
            id_to_info[vid] = (
                reg.document_id,
                doc.filename if doc else "",
                reg.page_id,
                page.page_num if page else 0,
                "image",
                None,
                reg.id,
                reg.label or "",
            )

    # Build result items in RRF order
    results = []
    for vid, rrf_score in merged[:top_k]:
        info = id_to_info.get(vid)
        if not info:
            continue
        doc_id, title, page_id, page_num, typ, chunk_id, region_id, snippet = info
        results.append(
            SearchResultItem(
                document_id=doc_id,
                document_title=title,
                page_id=page_id,
                page_num=page_num,
                result_type=typ,
                chunk_id=chunk_id,
                region_id=region_id,
                snippet=snippet,
                score=round(rrf_score, 4),
                vector_id=vid,
            )
        )
    logger.info("Hybrid search returned %s results for query=%s", len(results), query[:50])
    return SearchResponse(query=request.query, results=results)
