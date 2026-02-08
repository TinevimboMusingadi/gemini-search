"""
Vision processor: run Gemini detection on each page image, crop regions, return (label, box, crop_bytes).
Pipeline assigns region_id and persists crops via storage.
"""
import io
import logging
from typing import Any, List, Tuple

from PIL import Image

from multimodal_search.core.schemas.vision import DetectedRegion
from multimodal_search.services.gemini_client import detect_regions, get_gemini_client
from multimodal_search.utils.image_processing import crop_image

logger = logging.getLogger(__name__)


def process_page(
    image_bytes: bytes,
    page_id: int,
    document_id: int,
    img_width: int,
    img_height: int,
    gemini_client: Any | None = None,
) -> List[Tuple[str, List[float], bytes]]:
    """
    Detect regions on a page, crop each to PNG bytes.

    Args:
        image_bytes: Page image bytes (PNG)
        page_id: Page DB id (for logging)
        document_id: Document DB id (for logging)
        img_width: Image width (for box scaling)
        img_height: Image height
        gemini_client: Optional Gemini client

    Returns:
        List of (label, box_2d [y0,x0,y1,x1], crop_png_bytes).
        Pipeline will create Region rows and save crops via storage.
    """
    if gemini_client is None:
        gemini_client = get_gemini_client()
    regions = detect_regions(gemini_client, image_bytes)
    if not regions:
        logger.debug("No regions detected on page_id=%s", page_id)
        return []

    pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    out = []
    for r in regions:
        try:
            crop_pil = crop_image(pil, r.box_2d, img_height, img_width, normalized=False)
            buf = io.BytesIO()
            crop_pil.save(buf, format="PNG")
            out.append((r.label, r.box_2d, buf.getvalue()))
        except Exception as e:
            logger.warning("Failed to crop region %s on page_id=%s: %s", r.label, page_id, e)
    logger.info("Page_id=%s: detected %s regions, cropped %s", page_id, len(regions), len(out))
    return out
