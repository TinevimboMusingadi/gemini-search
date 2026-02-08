"""Pydantic models for document and page metadata."""

from typing import Optional

from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    """Document (PDF) metadata."""

    id: int
    file_hash: str
    filename: str
    total_pages: int
    storage_path: Optional[str] = None


class PageMetadata(BaseModel):
    """Single page metadata."""

    id: int
    document_id: int
    page_num: int
    image_path: Optional[str] = None
    ocr_text: Optional[str] = None


class DocumentCreate(BaseModel):
    """Input for creating a document record."""

    file_hash: str
    filename: str
    total_pages: int
    storage_path: Optional[str] = None
