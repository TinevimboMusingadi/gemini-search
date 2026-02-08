"""
Ingest route: POST PDF file or path to trigger indexing.
"""
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from multimodal_search.api.dependencies import get_db
from multimodal_search.indexer.pipeline import run_pipeline
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/pdf")
def ingest_pdf(
    file: UploadFile = File(...),
    session: Session = Depends(get_db),
):
    """Upload a PDF file for indexing. Returns document_id on success."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    try:
        content = file.file.read()
    except Exception as e:
        logger.exception("Failed to read uploaded file: %s", e)
        raise HTTPException(status_code=400, detail="Failed to read file")
    # Save to temp and run pipeline
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(content)
        path = Path(tmp.name)
    try:
        doc_id = run_pipeline(path, session=session)
        if doc_id is None:
            session.rollback()
            raise HTTPException(status_code=200, detail="Skipped (duplicate or empty)")
        session.commit()
        return {"document_id": doc_id, "status": "indexed"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Ingest failed: %s", e)
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        path.unlink(missing_ok=True)
