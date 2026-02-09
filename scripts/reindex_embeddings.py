#!/usr/bin/env python3
"""
Re-index embeddings from existing SQLite data to the Vector Store (ChromaDB).
Use this if:
1. You switched from memory to ChromaDB and lost in-memory vectors.
2. You want to re-generate embeddings without re-running OCR/Vision (expensive).

Run:
  uv run python scripts/reindex_embeddings.py
"""
import logging
import sys
import time
from pathlib import Path
from typing import List

# Ensure src is on path
_root = Path(__file__).resolve().parents[1]
if str(_root / "src") not in sys.path:
    sys.path.insert(0, str(_root / "src"))

from sqlalchemy import text
from sqlalchemy.orm import Session

from multimodal_search.core.config import get_settings
from multimodal_search.core.database import (
    Region,
    TextChunk,
    get_engine,
    get_session_factory,
    init_db,
)
from multimodal_search.core.vector_store import get_vector_store
from multimodal_search.services.vertex_embedder import embed_images, embed_text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("reindex")


def reindex_text_chunks(session: Session, batch_size: int = 50):
    """Fetch all text chunks, embed, and add to vector store."""
    vec_store = get_vector_store()
    total = session.query(TextChunk).count()
    logger.info("Found %d text chunks to re-index", total)
    
    offset = 0
    while offset < total:
        chunks = session.query(TextChunk).order_by(TextChunk.id).limit(batch_size).offset(offset).all()
        if not chunks:
            break
        
        texts = [c.text for c in chunks]
        ids = [c.vector_id for c in chunks]
        metadatas = [
            {"document_id": c.document_id, "page_id": c.page_id, "type": "text"}
            for c in chunks
        ]
        
        logger.info("Embedding text batch %d-%d / %d...", offset + 1, offset + len(chunks), total)
        try:
            vectors = embed_text(texts)
            if len(vectors) == len(ids):
                vec_store.add(ids, vectors, metadata=metadatas)
                logger.info("Saved batch to vector store")
            else:
                logger.error("Mismatch: %d ids vs %d vectors", len(ids), len(vectors))
        except Exception as e:
            logger.error("Failed batch %d: %s", offset, e)
        
        offset += len(chunks)


def reindex_regions(session: Session, batch_size: int = 20):
    """Fetch all regions, load images, embed, and add to vector store."""
    vec_store = get_vector_store()
    total = session.query(Region).count()
    logger.info("Found %d regions to re-index", total)
    
    offset = 0
    while offset < total:
        regions = session.query(Region).order_by(Region.id).limit(batch_size).offset(offset).all()
        if not regions:
            break
        
        valid_regions = []
        image_inputs = []
        ids = []
        metadatas = []
        
        for r in regions:
            if not r.crop_path:
                logger.warning("Region %s has no crop_path, skipping", r.id)
                continue
            p = Path(r.crop_path)
            if not p.exists():
                logger.warning("Region %s crop not found at %s, skipping", r.id, p)
                continue
            
            valid_regions.append(r)
            image_inputs.append(p)
            ids.append(r.vector_id)
            metadatas.append({
                "document_id": r.document_id,
                "page_id": r.page_id,
                "type": "image",
                "region_id": r.id
            })
            
        if not valid_regions:
            offset += len(regions)
            continue

        logger.info("Embedding region batch %d-%d / %d...", offset + 1, offset + len(regions), total)
        try:
            vectors = embed_images(image_inputs)
            if len(vectors) == len(ids):
                vec_store.add(ids, vectors, metadata=metadatas)
                logger.info("Saved batch to vector store")
            else:
                logger.error("Mismatch: %d ids vs %d vectors", len(ids), len(vectors))
        except Exception as e:
            logger.error("Failed batch %d: %s", offset, e)
            
        offset += len(regions)


def main():
    settings = get_settings()
    logger.info("Starting re-index. DB=%s, Backend=%s", settings.resolved_db_path, settings.vector_store_backend)
    
    if settings.vector_store_backend != "chroma":
        logger.warning("WARNING: vector_store_backend is '%s'. If this is 'memory', vectors will be lost on exit!", settings.vector_store_backend)
        logger.warning("Update config.py or .env to use 'chroma' if you want persistence.")
        time.sleep(2)

    engine = get_engine()
    init_db(engine)
    session_factory = get_session_factory(engine)
    session = session_factory()
    
    try:
        reindex_text_chunks(session)
        reindex_regions(session)
        logger.info("Re-indexing complete.")
    finally:
        session.close()


if __name__ == "__main__":
    main()
