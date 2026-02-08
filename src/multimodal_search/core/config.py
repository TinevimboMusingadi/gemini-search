"""
Application configuration via environment variables.
"""
import logging
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Load from env; see key_and_env_context.md for required vars."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # GCP
    gcp_project_id: Optional[str] = Field(default=None, description="GCP project for Vertex / Vision")
    gcp_location: str = Field(default="us-central1", description="Vertex AI region")
    google_application_credentials: Optional[str] = Field(
        default=None,
        description="Path to service account JSON",
    )

    # Vision: API key optional if using ADC
    google_api_key: Optional[str] = Field(default=None, description="Vision REST client API key")

    # Gemini
    gemini_api_key: Optional[str] = Field(default=None, description="Gemini API key from AI Studio")

    # Paths (relative to project root or absolute)
    project_root: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[3])
    data_dir: Path = Field(default=Path("data"), description="Base data directory")
    db_path: Path = Field(default=Path("multimodal_search.db"), description="SQLite DB path")
    pdfs_dir: str = Field(default="pdfs", description="Subdir under data_dir for PDFs")
    crops_dir: str = Field(default="crops", description="Subdir under data_dir for crops")

    # Indexing: Gemini detection (prompt1 / gemini_object_detection)
    bounding_box_system_instructions: str = Field(
        default="""Return bounding boxes as a JSON array with labels. Never return masks or code fencing. Limit to 25 objects.
If an object is present multiple times, name them according to their unique characteristics (colors, size, position, unique characteristics, etc.).""",
        description="System instruction for Gemini object detection",
    )
    pdf_spatial_instructions: Optional[str] = Field(
        default=None,
        description="Optional extra instructions for PDF page layout (figures, tables, diagrams)",
    )

    # OCR / pipeline
    ocr_batch_size: int = Field(default=12, ge=1, le=16, description="Vision API batch size for OCR")
    ocr_max_queue_size: int = Field(default=24, ge=1, description="Max queue size for turbo OCR pipeline")
    pdf_render_dpi: int = Field(default=144, ge=72, description="DPI for PDF page rendering")

    # Embeddings
    embedding_dimension: int = Field(default=1408, description="Vector dimension (Vertex multimodal 1408)")

    # Vector store: "memory" (in-memory) or "chroma" (local ChromaDB)
    vector_store_backend: str = Field(
        default="memory",
        description="Vector store backend: 'memory' or 'chroma'",
    )
    chroma_persist_dir: Path = Field(
        default=Path("data/chroma"),
        description="ChromaDB persistence directory (used when vector_store_backend=chroma)",
    )

    def __init__(self, **kwargs):  # type: ignore[no-untyped-def]
        super().__init__(**kwargs)
        logger.debug(
            "Config loaded: gcp_project_id=%s, gcp_location=%s, db_path=%s",
            self.gcp_project_id,
            self.gcp_location,
            self.db_path,
        )

    @property
    def resolved_db_path(self) -> Path:
        p = self.db_path
        if not p.is_absolute():
            p = self.project_root / p
        return p

    @property
    def resolved_data_dir(self) -> Path:
        p = self.data_dir
        if not p.is_absolute():
            p = self.project_root / p
        return p

    @property
    def resolved_pdfs_dir(self) -> Path:
        return self.resolved_data_dir / self.pdfs_dir

    @property
    def resolved_crops_dir(self) -> Path:
        return self.resolved_data_dir / self.crops_dir

    @property
    def resolved_chroma_dir(self) -> Path:
        p = self.chroma_persist_dir
        if not p.is_absolute():
            p = self.project_root / p
        return p


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Return singleton settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
        logger.info("Settings initialized; project_root=%s", _settings.project_root)
    return _settings
