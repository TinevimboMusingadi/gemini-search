"""
Storage abstraction for PDFs and cropped images.
Local implementation: data/pdfs/ and data/crops/ by document ID and crop ID.
"""
import hashlib
import logging
from pathlib import Path
from typing import BinaryIO, Optional, Union

from multimodal_search.core.config import get_settings

logger = logging.getLogger(__name__)


class StorageBackend:
    """Interface for saving and resolving PDF and crop paths."""

    def save_pdf(self, content: Union[bytes, BinaryIO], document_id: int, filename: str) -> Path:
        """Save PDF bytes to storage; return path. Uses document_id for directory."""
        raise NotImplementedError

    def save_crop(
        self,
        content: Union[bytes, BinaryIO],
        document_id: int,
        region_id: int,
        extension: str = "png",
    ) -> Path:
        """Save crop image; return path."""
        raise NotImplementedError

    def save_page(
        self,
        content: Union[bytes, BinaryIO],
        document_id: int,
        page_num: int,
        extension: str = "png",
    ) -> Path:
        """Save page image; return path."""
        raise NotImplementedError

    def get_pdf_path(self, document_id: int) -> Optional[Path]:
        """Return path to stored PDF if present."""
        raise NotImplementedError

    def get_crop_path(self, document_id: int, region_id: int) -> Optional[Path]:
        """Return path to stored crop if present."""
        raise NotImplementedError

    def ensure_dirs(self) -> None:
        """Create base directories if they do not exist."""
        raise NotImplementedError


class LocalStorage(StorageBackend):
    """Store PDFs and crops under data_dir/pdfs and data_dir/crops."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._base = self._settings.resolved_data_dir
        self._pdfs = self._settings.resolved_pdfs_dir
        self._crops = self._settings.resolved_crops_dir
        self._pages = self._base / "pages"

    def ensure_dirs(self) -> None:
        self._pdfs.mkdir(parents=True, exist_ok=True)
        self._crops.mkdir(parents=True, exist_ok=True)
        self._pages.mkdir(parents=True, exist_ok=True)
        logger.debug("Storage dirs ensured: %s, %s, %s", self._pdfs, self._crops, self._pages)

    def save_pdf(self, content: Union[bytes, BinaryIO], document_id: int, filename: str) -> Path:
        self.ensure_dirs()
        dir_path = self._pdfs / str(document_id)
        dir_path.mkdir(parents=True, exist_ok=True)
        safe_name = Path(filename).name or "document.pdf"
        out_path = dir_path / safe_name
        data = content.read() if hasattr(content, "read") else content
        out_path.write_bytes(data)
        logger.info("Saved PDF: document_id=%s path=%s", document_id, out_path)
        return out_path

    def save_crop(
        self,
        content: Union[bytes, BinaryIO],
        document_id: int,
        region_id: int,
        extension: str = "png",
    ) -> Path:
        self.ensure_dirs()
        dir_path = self._crops / str(document_id)
        dir_path.mkdir(parents=True, exist_ok=True)
        out_path = dir_path / f"region_{region_id}.{extension.lstrip('.')}"
        data = content.read() if hasattr(content, "read") else content
        out_path.write_bytes(data)
        logger.debug("Saved crop: document_id=%s region_id=%s path=%s", document_id, region_id, out_path)
        return out_path

    def save_page(
        self,
        content: Union[bytes, BinaryIO],
        document_id: int,
        page_num: int,
        extension: str = "png",
    ) -> Path:
        self.ensure_dirs()
        dir_path = self._pages / str(document_id)
        dir_path.mkdir(parents=True, exist_ok=True)
        out_path = dir_path / f"page_{page_num}.{extension.lstrip('.')}"
        data = content.read() if hasattr(content, "read") else content
        out_path.write_bytes(data)
        logger.info("Saved page image: document_id=%s page=%s path=%s", document_id, page_num, out_path)
        return out_path

    def get_pdf_path(self, document_id: int) -> Optional[Path]:
        dir_path = self._pdfs / str(document_id)
        if not dir_path.exists():
            return None
        for f in dir_path.iterdir():
            if f.suffix.lower() == ".pdf":
                return f
        return None

    def get_crop_path(self, document_id: int, region_id: int) -> Optional[Path]:
        path = self._crops / str(document_id) / f"region_{region_id}.png"
        return path if path.exists() else None


_storage: Optional[StorageBackend] = None


def get_storage() -> StorageBackend:
    """Return singleton storage backend (local by default)."""
    global _storage
    if _storage is None:
        _storage = LocalStorage()
        logger.info("Storage backend initialized (LocalStorage)")
    return _storage
