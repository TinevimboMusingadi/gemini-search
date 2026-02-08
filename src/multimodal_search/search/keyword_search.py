"""
Keyword search over text_chunks (FTS5) and document titles; optionally region labels.
Returns list of (document_id, document_title, page_id, page_num, result_type, chunk_id, region_id, snippet, score).
"""
import logging
from typing import List, Tuple

from sqlalchemy import text
from sqlalchemy.orm import Session

from multimodal_search.core.database import Document, Page, Region, TextChunk

logger = logging.getLogger(__name__)


def keyword_search(
    session: Session,
    query: str,
    top_k: int = 20,
    include_region_labels: bool = True,
) -> List[Tuple[int, str, int, int, str, int | None, int | None, str, float, str | None]]:
    """
    Search FTS5 on text_chunks and optionally region labels (LIKE).

    Returns:
        List of (document_id, document_title, page_id, page_num, result_type, chunk_id, region_id, snippet, rank_score, vector_id).
        result_type is "text" or "image". vector_id used for RRF merge with vector search.
    """
    if not query or not query.strip():
        logger.warning("Keyword search with empty query")
        return []

    results = []
    # FTS5 on text_chunks
    try:
        r = session.execute(
            text("""
                SELECT tc.id, tc.page_id, tc.document_id, tc.text,
                       p.page_num, d.filename, tc.vector_id
                FROM text_chunks_fts f
                JOIN text_chunks tc ON f.rowid = tc.id
                JOIN pages p ON tc.page_id = p.id
                JOIN documents d ON tc.document_id = d.id
                WHERE text_chunks_fts MATCH :q
                ORDER BY rank
                LIMIT :lim
            """),
            {"q": query, "lim": top_k},
        )
        rows = r.fetchall()
        for row in rows:
            chunk_id, page_id, doc_id, snippet, page_num, filename, vector_id = row
            results.append((doc_id, filename or "", page_id, page_num, "text", chunk_id, None, (snippet or "")[:500], 1.0, vector_id))
        logger.debug("Keyword FTS returned %s text hits", len(rows))
    except Exception as e:
        logger.warning("FTS keyword search failed (table may not exist yet): %s", e)

    # Region labels: simple LIKE search
    if include_region_labels and len(results) < top_k:
        r2 = (
            session.query(Region, Document, Page)
            .join(Document, Region.document_id == Document.id)
            .join(Page, Region.page_id == Page.id)
            .filter(Region.label.ilike(f"%{query}%"))
            .limit(top_k - len(results))
            .all()
        )
        for reg, doc, page in r2:
            results.append((reg.document_id, doc.filename or "", reg.page_id, page.page_num, "image", None, reg.id, reg.label, 0.9, reg.vector_id))
        logger.debug("Keyword region label returned %s hits", len(r2))

    # Sort by score desc and truncate
    results.sort(key=lambda x: x[8], reverse=True)
    return results[:top_k]
