"""
Text processor: OCR (batched via Vision API) and chunking.
OCR batching is used by the pipeline (turbo: producer feeds queue, consumer batches to Vision).
This module provides chunking of OCR text for embedding and DB.
"""
import logging
from typing import List, Tuple

from multimodal_search.core.config import get_settings

logger = logging.getLogger(__name__)

DEFAULT_CHUNK_SIZE = 512
DEFAULT_CHUNK_OVERLAP = 64


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> List[str]:
    """
    Split text into overlapping chunks (fixed size).
    Returns list of chunk strings.
    """
    if not text or not text.strip():
        return []
    text = text.strip()
    if len(text) <= chunk_size:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        start = end - overlap
        if start >= len(text):
            break
    logger.debug("Chunked text into %s chunks (size=%s, overlap=%s)", len(chunks), chunk_size, overlap)
    return chunks


def chunk_ocr_results(
    ocr_results: List[Tuple[int, int, str]],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> List[Tuple[int, int, int, str]]:
    """
    Build text chunks from OCR results per page.

    Args:
        ocr_results: List of (page_id, document_id, full_text)

    Returns:
        List of (page_id, document_id, chunk_index, text)
    """
    out = []
    for page_id, doc_id, full_text in ocr_results:
        for idx, c in enumerate(chunk_text(full_text or "", chunk_size=chunk_size, overlap=overlap)):
            out.append((page_id, doc_id, idx, c))
    logger.info("Chunked OCR into %s chunks across %s pages", len(out), len(ocr_results))
    return out
