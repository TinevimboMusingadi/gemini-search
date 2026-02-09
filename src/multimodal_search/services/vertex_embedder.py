"""
Vertex AI embeddings: text and image in same 1408-dim space (multimodalembedding).
Used for indexing (RETRIEVAL_DOCUMENT) and query (RETRIEVAL_QUERY) in search.
"""
import logging
import os
import tempfile
from pathlib import Path
from typing import List, Union

from multimodal_search.core.config import get_settings

logger = logging.getLogger(__name__)


def _ensure_vertex_init() -> None:
    settings = get_settings()
    if not settings.gcp_project_id:
        raise ValueError("GCP_PROJECT_ID is not set; cannot use Vertex AI")
    # Vertex SDK uses google.auth.default(); ensure ADC sees service account path from .env
    if settings.google_application_credentials and not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        path = Path(settings.google_application_credentials)
        if not path.is_absolute():
            path = settings.project_root / path
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(path)
    import vertexai
    try:
        vertexai.init(project=settings.gcp_project_id, location=settings.gcp_location)
        logger.debug("Vertex AI initialized: project=%s location=%s", settings.gcp_project_id, settings.gcp_location)
    except Exception as e:
        logger.exception("Vertex AI init failed: %s", e)
        raise


def get_multimodal_model():
    """Lazy-load Vertex MultiModalEmbeddingModel."""
    _ensure_vertex_init()
    from vertexai.vision_models import MultiModalEmbeddingModel
    model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding")
    logger.debug("MultiModalEmbeddingModel loaded")
    return model


import time
from google.api_core import exceptions

def embed_text(texts: List[str], dimension: int | None = None) -> List[List[float]]:
    """
    Embed text chunks (e.g. for index). Same semantic space as images (1408).
    Includes rate-limit handling (429).
    """
    if not texts:
        logger.warning("embed_text called with empty list")
        return []
    settings = get_settings()
    dim = dimension or settings.embedding_dimension
    model = get_multimodal_model()
    out = []
    
    for i, t in enumerate(texts):
        retries = 0
        max_retries = 5
        while True:
            try:
                emb = model.get_embeddings(contextual_text=t, dimension=dim)
                out.append(emb.text_embedding)
                break # Success, move to next text
            except exceptions.ResourceExhausted as e:
                retries += 1
                if retries > max_retries:
                    logger.error("Max retries exceeded for text chunk %s", i)
                    raise e
                wait_time = 2 ** retries # Exponential backoff: 2, 4, 8, 16...
                logger.warning("Quota exceeded (429). Retrying chunk %s in %s seconds...", i, wait_time)
                time.sleep(wait_time)
            except Exception as e:
                logger.exception("Vertex embed_text failed for chunk: %s", e)
                raise

    logger.debug("Embedded %s text chunks (dim=%s)", len(out), dim)
    return out


def embed_images(
    image_inputs: List[Union[str, bytes, Path]],
    dimension: int | None = None,
) -> List[List[float]]:
    """
    Embed images (crop paths or bytes). Returns list of 1408-dim vectors.
    image_inputs: list of file path (str/Path) or image bytes.
    Includes rate-limit handling (429).
    """
    if not image_inputs:
        logger.warning("embed_images called with empty list")
        return []
    from vertexai.vision_models import Image as VMImage
    settings = get_settings()
    dim = dimension or settings.embedding_dimension
    model = get_multimodal_model()
    out = []
    
    for i, inp in enumerate(image_inputs):
        retries = 0
        max_retries = 5
        while True:
            try:
                if isinstance(inp, bytes):
                    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                        f.write(inp)
                        path = f.name
                    try:
                        image = VMImage.load_from_file(path)
                    finally:
                        Path(path).unlink(missing_ok=True)
                else:
                    path = str(inp) if isinstance(inp, Path) else inp
                    image = VMImage.load_from_file(path)
                
                emb = model.get_embeddings(image=image, dimension=dim)
                out.append(emb.image_embedding)
                break # Success
            except exceptions.ResourceExhausted as e:
                retries += 1
                if retries > max_retries:
                    logger.error("Max retries exceeded for image input %s", i)
                    raise e
                wait_time = 2 ** retries
                logger.warning("Quota exceeded (429) for image. Retrying input %s in %s seconds...", i, wait_time)
                time.sleep(wait_time)
            except Exception as e:
                logger.exception("Vertex embed_images failed for input: %s", e)
                raise

    logger.debug("Embedded %s images (dim=%s)", len(out), dim)
    return out


def embed_query(query: str, dimension: int | None = None) -> List[float]:
    """
    Embed a single search query (for RETRIEVAL_QUERY semantics).
    Use for search engine when doing vector search.
    """
    settings = get_settings()
    dim = dimension or settings.embedding_dimension
    model = get_multimodal_model()
    emb = model.get_embeddings(contextual_text=query, dimension=dim)
    return emb.text_embedding
