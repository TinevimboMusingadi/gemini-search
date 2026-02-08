"""Pydantic models for bounding boxes and crop coordinates (Gemini detection output)."""

from typing import List

from pydantic import BaseModel, Field


# Coordinates are [y0, x0, y1, x1] with y-axis first (Gemini convention)
class BoundingBox(BaseModel):
    """2D box in pixel or normalized coordinates."""

    y0: float = Field(..., description="Top y")
    x0: float = Field(..., description="Left x")
    y1: float = Field(..., description="Bottom y")
    x1: float = Field(..., description="Right x")

    @classmethod
    def from_list(cls, coords: List[float]) -> "BoundingBox":
        """From [y0, x0, y1, x1] as returned by Gemini."""
        if len(coords) != 4:
            raise ValueError("Expected 4 values [y0, x0, y1, x1]")
        return cls(y0=coords[0], x0=coords[1], y1=coords[2], x1=coords[3])

    def to_list(self) -> List[float]:
        return [self.y0, self.x0, self.y1, self.x1]


class DetectedRegion(BaseModel):
    """One detected region from Gemini (figure, table, diagram) with box and label."""

    box_2d: List[float] = Field(..., description="[y0, x0, y1, x1]")
    label: str = Field(..., description="Short label from detection")

    def get_bbox(self) -> BoundingBox:
        return BoundingBox.from_list(self.box_2d)
