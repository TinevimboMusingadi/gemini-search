"""
Gemini API client for vision detection (object/figure/table on pages).
Output: list of { "box_2d": [y0, x0, y1, x1], "label": "..." }.
Uses config for system instructions; temperature=0.5, thinking_budget=0.
"""
import json
import logging
from typing import Any, List, Union

from google import genai
from google.genai import types

from multimodal_search.core.config import get_settings
from multimodal_search.core.schemas.vision import DetectedRegion

logger = logging.getLogger(__name__)

DEFAULT_DETECTION_PROMPT = (
    "Detect all figures, tables, diagrams, and notable images on this PDF page. "
    "Return bounding boxes and short descriptive labels for each."
)


def get_gemini_client() -> genai.Client:
    """Build Gemini client from GEMINI_API_KEY."""
    settings = get_settings()
    if not settings.gemini_api_key:
        raise ValueError("GEMINI_API_KEY is not set; cannot create Gemini client")
    logger.debug("Gemini client initialized with API key")
    return genai.Client(api_key=settings.gemini_api_key)


def detect_regions(
    client: genai.Client,
    image: Union[bytes, "Any"],  # PIL Image or bytes
    prompt: str = DEFAULT_DETECTION_PROMPT,
    system_instruction: str | None = None,
) -> List[DetectedRegion]:
    """
    Run object/figure/table detection on a single page image.

    Args:
        client: Gemini client
        image: Page image as bytes or PIL Image
        prompt: User prompt for detection
        system_instruction: Override from config if None

    Returns:
        List of DetectedRegion (box_2d + label). Empty list on parse error.
    """
    settings = get_settings()
    sys_instr = system_instruction or settings.bounding_box_system_instructions
    if settings.pdf_spatial_instructions:
        sys_instr = sys_instr + "\n" + settings.pdf_spatial_instructions

    # Build content: text + image
    parts = [types.Part(text=prompt)]
    if isinstance(image, bytes):
        parts.append(types.Part(inline_data=types.Blob(mime_type="image/png", data=image)))
    else:
        # Assume PIL Image
        import io
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        parts.append(types.Part(inline_data=types.Blob(mime_type="image/png", data=buf.getvalue())))

    safety = [
        types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_ONLY_HIGH"),
    ]

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[types.Content(parts=parts)],
            config=types.GenerateContentConfig(
                system_instruction=sys_instr,
                temperature=0.5,
                safety_settings=safety,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
    except Exception as e:
        logger.exception("Gemini generate_content failed: %s", e)
        raise

    text = response.text if response and response.text else ""
    if not text.strip():
        logger.warning("Gemini detection returned empty text")
        return []

    # Strip markdown code fences
    raw = text.replace("```json", "").replace("```", "").strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.warning("Gemini detection response is not valid JSON: %s. Raw: %s", e, raw[:200])
        return []

    if not isinstance(data, list):
        logger.warning("Gemini detection response is not a list: %s", type(data))
        return []

    regions = []
    for item in data:
        if not isinstance(item, dict) or "box_2d" not in item or "label" not in item:
            continue
        try:
            regions.append(DetectedRegion(box_2d=item["box_2d"], label=item["label"]))
        except Exception as e:
            logger.debug("Skip invalid region item %s: %s", item, e)
    logger.debug("Detected %s regions on page", len(regions))
    return regions
