"""
Image cropping for detected regions: crop by bounding box, save to path.
Used for saving crops under data/crops/.
"""
import io
import logging
from pathlib import Path
from typing import List, Union

from PIL import Image

from multimodal_search.utils.geometry import box_to_pixels

logger = logging.getLogger(__name__)


def crop_image(
    image: Union[Image.Image, bytes],
    box: List[float],
    img_height: int,
    img_width: int,
    normalized: bool = False,
) -> Image.Image:
    """
    Crop image to bounding box [y0, x0, y1, x1].
    Returns PIL Image of the crop.
    """
    if isinstance(image, bytes):
        image = Image.open(io.BytesIO(image)).convert("RGB")
    elif not isinstance(image, Image.Image):
        raise TypeError("image must be PIL Image or bytes")
    py0, px0, py1, px1 = box_to_pixels(box, img_height, img_width, normalized=normalized)
    if py0 >= py1 or px0 >= px1:
        logger.warning("Empty or invalid crop box: (%s,%s,%s,%s)", py0, px0, py1, px1)
        return image.crop((0, 0, 1, 1))  # minimal 1px crop to avoid errors
    return image.crop((px0, py0, px1, py1))


def crop_and_save(
    image: Union[Image.Image, bytes],
    box: List[float],
    img_height: int,
    img_width: int,
    save_path: Union[str, Path],
    format: str = "PNG",
    normalized: bool = False,
) -> Path:
    """
    Crop image to box and save to save_path. Returns path.
    """
    pil = crop_image(image, box, img_height, img_width, normalized=normalized)
    path = Path(save_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pil.save(path, format=format)
    logger.debug("Saved crop to %s", path)
    return path
