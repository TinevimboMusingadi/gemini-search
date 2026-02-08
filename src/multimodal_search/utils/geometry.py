"""
Bounding box math: normalized <-> pixel coordinates, scaling.
Gemini uses [y0, x0, y1, x1] with y-axis first.
"""
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)


def scale_box_to_pixels(
    y0: float,
    x0: float,
    y1: float,
    x1: float,
    img_height: int,
    img_width: int,
    normalized: bool = True,
) -> Tuple[int, int, int, int]:
    """
    Convert box to pixel coordinates (clamped to image bounds).

    If normalized is True, inputs are in [0, 1]; else they are already in pixel space.
    Returns (y0, x0, y1, x1) as integers.
    """
    if normalized:
        py0 = int(y0 * img_height)
        px0 = int(x0 * img_width)
        py1 = int(y1 * img_height)
        px1 = int(x1 * img_width)
    else:
        py0, px0, py1, px1 = int(y0), int(x0), int(y1), int(x1)
    # Clamp
    py0 = max(0, min(py0, img_height - 1))
    px0 = max(0, min(px0, img_width - 1))
    py1 = max(0, min(py1, img_height))
    px1 = max(0, min(px1, img_width))
    if py0 >= py1 or px0 >= px1:
        logger.warning("Invalid box after clamp: (%s,%s,%s,%s) -> (%s,%s,%s,%s)", y0, x0, y1, x1, py0, px0, py1, px1)
    return (py0, px0, py1, px1)


def box_to_pixels(
    box: List[float],
    img_height: int,
    img_width: int,
    normalized: bool = False,
) -> Tuple[int, int, int, int]:
    """
    Convert [y0, x0, y1, x1] to pixel coords.
    If normalized, box is in [0,1]; else in same units as image dimensions.
    """
    if len(box) != 4:
        raise ValueError("box must have 4 elements [y0, x0, y1, x1]")
    return scale_box_to_pixels(
        box[0], box[1], box[2], box[3],
        img_height, img_width, normalized=normalized,
    )


def normalize_box(
    y0: int, x0: int, y1: int, x1: int,
    img_height: int, img_width: int,
) -> Tuple[float, float, float, float]:
    """Convert pixel box to normalized [0,1] (y0, x0, y1, x1)."""
    return (
        y0 / img_height if img_height else 0,
        x0 / img_width if img_width else 0,
        y1 / img_height if img_height else 0,
        x1 / img_width if img_width else 0,
    )
