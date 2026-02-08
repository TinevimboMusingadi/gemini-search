"""
Render route: GET /render/{type}/{id} for page image or crop image (for UI).
"""
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from multimodal_search.api.dependencies import get_db
from multimodal_search.core.database import Page, Region
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/render", tags=["render"])


@router.get("/crop/{document_id}/{region_id}")
def render_crop(
    document_id: int,
    region_id: int,
    session: Session = Depends(get_db),
):
    """Return crop image file for a region."""
    reg = session.query(Region).filter(
        Region.document_id == document_id,
        Region.id == region_id,
    ).first()
    if not reg or not reg.crop_path:
        raise HTTPException(status_code=404, detail="Crop not found")
    path = Path(reg.crop_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Crop file not found")
    return FileResponse(path, media_type="image/png")


@router.get("/page/{document_id}/{page_num}")
def render_page(
    document_id: int,
    page_num: int,
    session: Session = Depends(get_db),
):
    """Return page image if stored. (Indexer may not store page images; endpoint for future use.)"""
    page = session.query(Page).filter(
        Page.document_id == document_id,
        Page.page_num == page_num,
    ).first()
    if not page or not page.image_path:
        raise HTTPException(status_code=404, detail="Page image not found")
    path = Path(page.image_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Page file not found")
    return FileResponse(path, media_type="image/png")
