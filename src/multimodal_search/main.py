"""
FastAPI application entrypoint.
Run with: uvicorn multimodal_search.main:app --reload
"""
import logging
import os

from fastapi import FastAPI

from multimodal_search.api.middleware.cors import add_cors
from multimodal_search.api.routes import chat, ingest, render, search_routes

_LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
_level = getattr(logging, _LOG_LEVEL, logging.INFO)
logging.basicConfig(
    level=_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Multimodal PDF Search API",
    description="Index PDFs (OCR + vision detection + embeddings), hybrid search, and Gemini agent.",
    version="0.1.0",
)

add_cors(app)

app.include_router(ingest.router)
app.include_router(search_routes.router)
app.include_router(chat.router)
app.include_router(render.router)


@app.get("/health")
def health():
    return {"status": "ok"}
