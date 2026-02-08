"""
Web search adapter using Gemini with Google Search grounding.
Returns response text and grounding metadata (sources, URIs) for the agent.
"""
import logging
from dataclasses import dataclass
from typing import Any, List, Optional

from google import genai
from google.genai import types

from multimodal_search.services.gemini_client import get_gemini_client

logger = logging.getLogger(__name__)


@dataclass
class GroundingChunk:
    """One web source from grounding."""

    title: Optional[str] = None
    uri: Optional[str] = None


@dataclass
class WebSearchResult:
    """Result of a web-grounded Gemini call."""

    text: str
    web_search_queries: List[str]
    grounding_chunks: List[GroundingChunk]
    raw_metadata: Optional[Any] = None


def web_search(query: str, client: Optional[genai.Client] = None) -> WebSearchResult:
    """
    Call Gemini with Google Search grounding for the given query.

    Args:
        query: User search question
        client: Optional Gemini client (uses get_gemini_client() if None)

    Returns:
        WebSearchResult with text, queries executed, and source chunks (title, URI).
    """
    if client is None:
        client = get_gemini_client()
    grounding_tool = types.Tool(google_search=types.GoogleSearch())
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=query,
            config=types.GenerateContentConfig(tools=[grounding_tool]),
        )
    except Exception as e:
        logger.exception("Web search (Gemini grounding) failed: %s", e)
        raise

    text = response.text if response and response.text else ""
    web_queries: List[str] = []
    chunks: List[GroundingChunk] = []

    if response and response.candidates:
        cand = response.candidates[0]
        if getattr(cand, "grounding_metadata", None):
            meta = cand.grounding_metadata
            if getattr(meta, "web_search_queries", None):
                web_queries = list(meta.web_search_queries)
            if getattr(meta, "grounding_chunks", None):
                for c in meta.grounding_chunks:
                    web = getattr(c, "web", None)
                    title = getattr(web, "title", None) if web else None
                    uri = getattr(web, "uri", None) if web else None
                    chunks.append(GroundingChunk(title=title, uri=uri))
            logger.debug("Web search: queries=%s, chunks=%s", len(web_queries), len(chunks))

    return WebSearchResult(
        text=text,
        web_search_queries=web_queries,
        grounding_chunks=chunks,
        raw_metadata=getattr(response.candidates[0], "grounding_metadata", None) if response.candidates else None,
    )
