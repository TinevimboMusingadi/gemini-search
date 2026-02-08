"""
PDF processor: load PDF (pypdfium2), render each page to image, return list of (page_index, image_bytes, metadata).
Single source of pages for OCR and vision.
"""
import io
import logging
from pathlib import Path
from typing import List, Tuple, Union

import pypdfium2 as pdfium

from multimodal_search.core.config import get_settings

logger = logging.getLogger(__name__)


def render_pdf_pages(
    pdf_path: Union[str, Path],
    dpi: int | None = None,
) -> List[Tuple[int, bytes, dict]]:
    """
    Render each PDF page to PNG bytes.

    Args:
        pdf_path: Path to PDF file
        dpi: Render resolution (default from config, e.g. 144)

    Returns:
        List of (page_index_0based, image_bytes, metadata).
        metadata has "page_num" (1-based), "width", "height".
    """
    settings = get_settings()
    scale = (dpi or settings.pdf_render_dpi) / 72.0
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    pdf = pdfium.PdfDocument(str(path))
    try:
        num_pages = len(pdf)
        logger.info("PDF %s: %s pages, rendering at %.0f DPI", path.name, num_pages, dpi or settings.pdf_render_dpi)
        out = []
        for i in range(num_pages):
            page = pdf.get_page(i)
            bitmap = page.render(scale=scale)
            pil = bitmap.to_pil()
            buf = io.BytesIO()
            pil.save(buf, format="PNG")
            img_bytes = buf.getvalue()
            meta = {
                "page_num": i + 1,
                "width": pil.width,
                "height": pil.height,
            }
            out.append((i, img_bytes, meta))
            logger.debug("Rendered page %s (%sx%s)", i + 1, pil.width, pil.height)
        return out
    finally:
        pdf.close()


def load_pdf_page_count(pdf_path: Union[str, Path]) -> int:
    """Return number of pages without rendering."""
    path = Path(pdf_path)
    pdf = pdfium.PdfDocument(str(path))
    try:
        return len(pdf)
    finally:
        pdf.close()
