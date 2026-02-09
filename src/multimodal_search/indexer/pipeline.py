"""
Orchestrates full indexing pipeline: PDF -> pages -> OCR (turbo) -> vision -> crops -> embed -> DB + vector store + storage.
"""
import hashlib
import logging
import queue
import threading
from pathlib import Path
from typing import List, Optional, Tuple, Union

from sqlalchemy.orm import Session

from multimodal_search.core.config import get_settings
from multimodal_search.core.database import (
    Document,
    Page,
    Region,
    TextChunk,
    get_engine,
    get_session_factory,
    init_db,
)
from multimodal_search.core.storage import get_storage
from multimodal_search.core.vector_store import get_vector_store
from multimodal_search.indexer.processors.pdf_processor import render_pdf_pages
from multimodal_search.indexer.processors.text_processor import chunk_ocr_results
from multimodal_search.indexer.processors.vision_processor import process_page
from multimodal_search.services.gcp_vision import batch_ocr, get_vision_client
from multimodal_search.services.gemini_client import get_gemini_client
from multimodal_search.services.vertex_embedder import embed_images, embed_text

logger = logging.getLogger(__name__)


def _ocr_consumer(
    vision_client,
    task_queue: queue.Queue,
    results_list: list,
    batch_size: int,
    stop_event: threading.Event,
) -> None:
    """Consume (page_num, img_bytes, page_id, doc_id) from queue, batch OCR, append (page_id, doc_id, text)."""
    while not stop_event.is_set():
        batch = []
        for _ in range(batch_size):
            try:
                item = task_queue.get(timeout=1)
                if item is None:
                    break
                batch.append(item)
            except queue.Empty:
                break
        if not batch:
            if item is None:
                break
            continue
        if item is None and batch:
            pass  # batch has items
        page_nums = [x[0] for x in batch]
        img_bytes_list = [x[1] for x in batch]
        page_ids = [x[2] for x in batch]
        doc_ids = [x[3] for x in batch]
        try:
            ocr_results = batch_ocr(vision_client, img_bytes_list)
            for i, (_, full_text, err) in enumerate(ocr_results):
                if i < len(page_ids):
                    results_list.append((page_ids[i], doc_ids[i], full_text if not err else ""))
            logger.debug("OCR batch done: %s pages", len(batch))
        except Exception as e:
            logger.exception("OCR batch failed: %s", e)
            for i in range(len(batch)):
                results_list.append((page_ids[i], doc_ids[i], ""))


import concurrent.futures

def run_pipeline(
    pdf_path: Union[str, Path],
    session: Optional[Session] = None,
) -> Optional[int]:
    """
    Run full index pipeline on a PDF. Returns document_id on success, None if skipped (duplicate) or error.

    Steps:
    1) Hash, check duplicate, render pages
    2) Insert Document + Pages + Save Page Images
    3) Parallel Extraction:
       - Turbo OCR (background thread)
       - Vision Detection (ThreadPoolExecutor)
    4) Synchronization: Wait for both
    5) Sequential Embedding:
       - Embed text chunks (Vertex AI) -> DB + Vector Store
       - Embed crop images (Vertex AI) -> DB + Vector Store
    6) Save PDF to storage
    """
    path = Path(pdf_path)
    if not path.exists():
        logger.error("PDF not found: %s", path)
        return None

    settings = get_settings()
    file_hash = hashlib.sha256(path.read_bytes()).hexdigest()

    use_external_session = session is not None
    if not use_external_session:
        engine = get_engine()
        init_db(engine)
        session_factory = get_session_factory(engine)
        session = session_factory()

    try:
        # Duplicate check
        existing = session.query(Document).filter(Document.file_hash == file_hash).first()
        if existing:
            logger.info("Skipping duplicate PDF: %s (doc_id=%s)", path.name, existing.id)
            return existing.id

        # Render pages
        logger.info("Rendering PDF: %s", path.name)
        pages_data = render_pdf_pages(path)
        if not pages_data:
            logger.warning("No pages rendered: %s", path.name)
            return None

        # Insert document
        doc = Document(
            file_hash=file_hash,
            filename=path.name,
            total_pages=len(pages_data),
        )
        session.add(doc)
        session.flush()
        document_id = doc.id
        logger.info("Created document id=%s", document_id)

        # Save page images to storage
        storage = get_storage()
        storage.ensure_dirs()
        for i, (_, img_bytes, meta) in enumerate(pages_data):
            storage.save_page(img_bytes, document_id, meta["page_num"])

        # Insert page records
        page_id_by_index = []
        for i, (_, _, meta) in enumerate(pages_data):
            p = Page(document_id=document_id, page_num=meta["page_num"])
            session.add(p)
            session.flush()
            page_id_by_index.append(p.id)

        # --- Parallel Extraction Start ---
        
        # 1. Start OCR (Thread)
        vision_client = get_vision_client()
        task_queue = queue.Queue(maxsize=settings.ocr_max_queue_size)
        ocr_results_list = []
        stop_event = threading.Event()
        ocr_consumer_thread = threading.Thread(
            target=_ocr_consumer,
            args=(vision_client, task_queue, ocr_results_list, settings.ocr_batch_size, stop_event),
        )
        ocr_consumer_thread.start()
        
        # Feed OCR queue
        for i, (_, img_bytes, meta) in enumerate(pages_data):
            page_id = page_id_by_index[i]
            task_queue.put((meta["page_num"], img_bytes, page_id, document_id))
        task_queue.put(None) # Signal end of OCR tasks

        # 2. Start Vision Detection (ThreadPool)
        gemini_client = get_gemini_client()
        vision_results = [None] * len(pages_data) # Store results by index

        def _process_page_wrapper(idx, img_bytes, page_id, w, h):
            try:
                return idx, process_page(img_bytes, page_id, document_id, w, h, gemini_client)
            except Exception as e:
                logger.exception("Vision detection failed for page %s: %s", page_id, e)
                return idx, []

        # Use ThreadPoolExecutor for concurrent Gemini calls
        # Adjust max_workers based on rate limits if needed, default to 4 or 8 is usually fine for IO
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_page = {
                executor.submit(
                    _process_page_wrapper, 
                    i, 
                    pages_data[i][1], 
                    page_id_by_index[i], 
                    pages_data[i][2]["width"], 
                    pages_data[i][2]["height"]
                ): i for i in range(len(pages_data))
            }
            for future in concurrent.futures.as_completed(future_to_page):
                idx, regions = future.result()
                vision_results[idx] = regions

        # Wait for OCR to finish
        ocr_consumer_thread.join()
        
        # --- Parallel Extraction End ---

        # Process OCR Results
        page_text_map = {r[0]: (r[1], r[2]) for r in ocr_results_list}
        for page in session.query(Page).filter(Page.document_id == document_id):
            if page.id in page_text_map:
                _, text = page_text_map[page.id]
                page.ocr_text = text
        session.flush()

        ocr_for_chunking = [(pid, doc_id, text) for pid, doc_id, text in ocr_results_list]
        chunks = chunk_ocr_results(ocr_for_chunking)
        
        # Embed text chunks (Sequential)
        vec_store = get_vector_store()
        if chunks:
            chunk_texts = [c[3] for c in chunks]
            vectors = embed_text(chunk_texts)
            chunk_ids = []
            meta_list = []
            for (page_id, doc_id, chunk_idx, text) in chunks:
                vector_id = f"chunk_{document_id}_{page_id}_{chunk_idx}"
                meta_list.append({"document_id": document_id, "page_id": page_id, "type": "text"})
                chunk_ids.append(vector_id)
            vec_store.add(chunk_ids, vectors, metadata=meta_list)
            for idx, (page_id, doc_id, chunk_idx, text) in enumerate(chunks):
                vector_id = chunk_ids[idx]
                tc = TextChunk(
                    page_id=page_id,
                    document_id=doc_id,
                    chunk_index=chunk_idx,
                    text=text,
                    vector_id=vector_id,
                )
                session.add(tc)
                session.flush()
            logger.info("Indexed %s text chunks for doc_id=%s", len(chunks), document_id)

        # Process Vision Results & Embed Images (Sequential)
        all_region_vectors = []
        all_region_ids = []
        all_region_meta = []
        
        # Flatten results and save crops
        for i, region_tuples in enumerate(vision_results):
            if not region_tuples:
                continue
            page_id = page_id_by_index[i]
            
            for label, box_2d, crop_bytes in region_tuples:
                r = Region(
                    page_id=page_id,
                    document_id=document_id,
                    label=label,
                    box_y0=box_2d[0],
                    box_x0=box_2d[1],
                    box_y1=box_2d[2],
                    box_x1=box_2d[3],
                )
                session.add(r)
                session.flush()
                region_id = r.id
                crop_path = storage.save_crop(crop_bytes, document_id, region_id)
                r.crop_path = str(crop_path)
                vector_id = f"region_{document_id}_{region_id}"
                r.vector_id = vector_id
                all_region_ids.append(vector_id)
                all_region_meta.append({"document_id": document_id, "page_id": page_id, "type": "image", "region_id": region_id})
                
                # Collect for batch embedding
                # Note: We can batch all crops from all pages or do per-page. 
                # Doing all at once allows larger batches if needed, but we already have retry logic.
                # Let's just collect crop bytes.
                all_region_vectors.append(crop_bytes) # temporarily store bytes here

        # Embed all collected crops
        if all_region_vectors:
            # Actually embed the bytes now
            # embed_images now has backoff logic
            embeddings = embed_images(all_region_vectors)
            
            if len(embeddings) == len(all_region_ids):
                vec_store.add(all_region_ids, embeddings, metadata=all_region_meta)
                logger.info("Indexed %s region (image) vectors for doc_id=%s", len(embeddings), document_id)
            else:
                logger.error("Mismatch in image embeddings: %s ids vs %s vectors", len(all_region_ids), len(embeddings))

        # Save PDF to storage
        pdf_bytes = path.read_bytes()
        stored_path = storage.save_pdf(pdf_bytes, document_id, path.name)
        doc.storage_path = str(stored_path)
        if not use_external_session:
            session.commit()
        logger.info("Pipeline complete: document_id=%s", document_id)
        return document_id
    except Exception as e:
        logger.exception("Pipeline failed: %s", e)
        if not use_external_session:
            session.rollback()
        raise
    finally:
        if not use_external_session and session:
            session.close()
