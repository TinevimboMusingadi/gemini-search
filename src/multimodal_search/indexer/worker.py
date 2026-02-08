"""
Background job runner for indexing. Stub: runs pipeline synchronously.
Can be extended with Celery/Redis or a simple queue later.
"""
import logging
from pathlib import Path
from typing import Optional, Union

from multimodal_search.indexer.pipeline import run_pipeline

logger = logging.getLogger(__name__)


def index_pdf(pdf_path: Union[str, Path], session: Optional[object] = None) -> Optional[int]:
    """
    Index a single PDF (synchronous). Returns document_id on success, None if skipped or error.
    """
    logger.info("Worker indexing PDF: %s", pdf_path)
    try:
        doc_id = run_pipeline(pdf_path, session=session)
        logger.info("Worker finished: pdf=%s -> doc_id=%s", pdf_path, doc_id)
        return doc_id
    except Exception as e:
        logger.exception("Worker failed for %s: %s", pdf_path, e)
        raise
