"""
Document routes: list documents, get document detail, get page regions.
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from multimodal_search.api.dependencies import get_db
from multimodal_search.core.database import Document, Page, Region

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])


# ---------- Response schemas ----------


class DocumentListItem(BaseModel):
    id: int
    filename: str
    total_pages: int
    storage_path: Optional[str] = None


class PageSummary(BaseModel):
    id: int
    page_num: int
    has_image: bool
    has_ocr_text: bool


class DocumentDetail(BaseModel):
    id: int
    filename: str
    total_pages: int
    storage_path: Optional[str] = None
    pages: List[PageSummary]


class RegionDetail(BaseModel):
    id: int
    page_id: int
    label: str
    box_y0: float
    box_x0: float
    box_y1: float
    box_x1: float
    crop_path: Optional[str] = None
    vector_id: Optional[str] = None


# ---------- Endpoints ----------


@router.get("", response_model=List[DocumentListItem])
def list_documents(session: Session = Depends(get_db)):
    """List all indexed documents."""
    docs = session.query(Document).order_by(Document.id.desc()).all()
    return [
        DocumentListItem(
            id=d.id,
            filename=d.filename,
            total_pages=d.total_pages,
            storage_path=d.storage_path,
        )
        for d in docs
    ]


@router.get("/{document_id}", response_model=DocumentDetail)
def get_document(document_id: int, session: Session = Depends(get_db)):
    """Get a single document with its page list."""
    doc = session.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    pages = (
        session.query(Page)
        .filter(Page.document_id == document_id)
        .order_by(Page.page_num.asc())
        .all()
    )

    return DocumentDetail(
        id=doc.id,
        filename=doc.filename,
        total_pages=doc.total_pages,
        storage_path=doc.storage_path,
        pages=[
            PageSummary(
                id=p.id,
                page_num=p.page_num,
                has_image=bool(p.image_path),
                has_ocr_text=bool(p.ocr_text),
            )
            for p in pages
        ],
    )


@router.get(
    "/{document_id}/pages/{page_num}/regions",
    response_model=List[RegionDetail],
)
def get_page_regions(
    document_id: int,
    page_num: int,
    session: Session = Depends(get_db),
):
    """Get all detected regions for a specific page."""
    page = (
        session.query(Page)
        .filter(Page.document_id == document_id, Page.page_num == page_num)
        .first()
    )
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    regions = (
        session.query(Region)
        .filter(Region.page_id == page.id, Region.document_id == document_id)
        .order_by(Region.id.asc())
        .all()
    )

    return [
        RegionDetail(
            id=r.id,
            page_id=r.page_id,
            label=r.label,
            box_y0=r.box_y0,
            box_x0=r.box_x0,
            box_y1=r.box_y1,
            box_x1=r.box_x1,
            crop_path=r.crop_path,
            vector_id=r.vector_id,
        )
        for r in regions
    ]
