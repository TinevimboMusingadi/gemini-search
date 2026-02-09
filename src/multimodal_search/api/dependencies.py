"""
FastAPI dependencies: config, DB session, storage, vector store, services, search engine, agent.
"""
import logging
from typing import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from multimodal_search.agent.chains import run_agent
from multimodal_search.core.config import get_settings, Settings
from multimodal_search.core.database import get_engine, get_session_factory, init_db
from multimodal_search.core.storage import get_storage
from multimodal_search.core.vector_store import get_vector_store
from multimodal_search.search.engine import search as search_engine_search
from multimodal_search.core.schemas.search import SearchRequest, SearchResponse
from multimodal_search.services.gcp_vision import get_vision_client
from multimodal_search.services.gemini_client import get_gemini_client
from multimodal_search.services.web_search import web_search

logger = logging.getLogger(__name__)


def get_config() -> Settings:
    return get_settings()


def _ensure_db_ready() -> None:
    """One-time DB + FTS5 bootstrap (idempotent, cached internally)."""
    engine = get_engine()
    init_db(engine)


# Run once at import time so first request isn't slow
_ensure_db_ready()


def get_db() -> Generator[Session, None, None]:
    """Yield a DB session per request."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
    finally:
        session.close()


def get_storage_backend():
    return get_storage()


def get_vec_store():
    return get_vector_store()


def get_vision():
    return get_vision_client()


def get_gemini():
    return get_gemini_client()


def get_search_engine(session: Session = Depends(get_db)):
    """Return a callable (SearchRequest) -> SearchResponse that uses the current session."""
    def _search(req: SearchRequest) -> SearchResponse:
        return search_engine_search(session, req)
    return _search


def get_agent_runner(
    session: Session = Depends(get_db),
    search_fn=Depends(get_search_engine),
):
    """Return run_agent bound with session and search_engine_fn."""
    def _run(message: str, selected_region_context: str | None = None, session_id: str | None = None):
        return run_agent(
            message,
            session=session,
            search_engine_fn=search_fn,
            selected_region_context=selected_region_context,
            session_id=session_id,
        )
    return _run
