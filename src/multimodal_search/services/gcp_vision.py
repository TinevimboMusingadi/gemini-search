"""
GCP Cloud Vision API adapter for OCR.
Uses DOCUMENT_TEXT_DETECTION and batch_annotate_images (batch size 12-16).
Caller passes page images; no PDF splitting here.
"""
import logging
from typing import List, Optional, Tuple

from google.cloud import vision
from google.api_core.client_options import ClientOptions

from multimodal_search.core.config import get_settings

logger = logging.getLogger(__name__)

# Sentinel for batch end in consumer
OCR_BATCH_SIZE_MAX = 16


def get_vision_client() -> vision.ImageAnnotatorClient:
    """Build Vision client: API key if set, else ADC (GOOGLE_APPLICATION_CREDENTIALS)."""
    settings = get_settings()
    if settings.google_api_key:
        logger.info("Vision client: using API key")
        return vision.ImageAnnotatorClient(
            client_options=ClientOptions(api_key=settings.google_api_key)
        )
    logger.info("Vision client: using Application Default Credentials")
    return vision.ImageAnnotatorClient()


def batch_ocr(
    client: vision.ImageAnnotatorClient,
    image_bytes_list: List[bytes],
) -> List[Tuple[int, str, Optional[str]]]:
    """
    Run DOCUMENT_TEXT_DETECTION on a batch of images.

    Args:
        client: Vision API client
        image_bytes_list: List of image bytes (e.g. PNG/JPEG per page)

    Returns:
        List of (index, full_text, error_message). error_message is None on success.
        Order matches image_bytes_list.
    """
    if not image_bytes_list:
        logger.warning("batch_ocr called with empty image list")
        return []

    requests = []
    for i, img_bytes in enumerate(image_bytes_list):
        image = vision.Image(content=img_bytes)
        features = [vision.Feature(type_=vision.Feature.Type.DOCUMENT_TEXT_DETECTION)]
        requests.append(vision.AnnotateImageRequest(image=image, features=features))

    try:
        response = client.batch_annotate_images(requests=requests)
        logger.debug("Vision batch_annotate_images returned %s responses", len(response.responses))
    except Exception as e:
        logger.exception("Vision API batch_annotate_images failed: %s", e)
        raise

    results = []
    for i, res in enumerate(response.responses):
        if res.error.message:
            logger.warning("Vision OCR error for image %s: %s", i, res.error.message)
            results.append((i, "", res.error.message))
            continue
        full_text = res.full_text_annotation.text if res.full_text_annotation else ""
        results.append((i, full_text, None))
    return results
