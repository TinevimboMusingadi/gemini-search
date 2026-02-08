"""
Agent tools: SearchDB (search_local_index) and WebSearch.
Function declarations for Gemini and implementations.
"""
import logging
from typing import Any, Callable, Optional

from google.genai import types

from multimodal_search.core.schemas.search import SearchRequest, SearchResponse

logger = logging.getLogger(__name__)

SEARCH_DB_FUNCTION = types.FunctionDeclaration(
    name="search_local_index",
    description="Search the local PDF index by keyword and semantics. Returns matching text snippets and figure/table labels from indexed documents.",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query (keywords or natural language question)",
            },
            "top_k": {
                "type": "integer",
                "description": "Maximum number of results to return (default 10)",
            },
        },
        "required": ["query"],
    },
)

WEB_SEARCH_FUNCTION = types.FunctionDeclaration(
    name="web_search",
    description="Search the web for current or general information. Use for facts, recent events, or information not in the local PDF index.",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search question or keywords",
            },
        },
        "required": ["query"],
    },
)


def get_search_tool_declarations() -> list:
    """Return list of Tool with function_declarations for Gemini."""
    return [
        types.Tool(function_declarations=[SEARCH_DB_FUNCTION, WEB_SEARCH_FUNCTION]),
    ]


def execute_search_local(
    query: str,
    top_k: int = 10,
    search_fn: Optional[Callable[..., SearchResponse]] = None,
) -> str:
    """Execute local search and return a string summary for the agent."""
    if search_fn is None:
        return "Error: search engine not configured"
    try:
        req = SearchRequest(query=query, top_k=top_k)
        resp = search_fn(req)
        if not resp.results:
            return "No results found in the local index."
        lines = []
        for r in resp.results[:top_k]:
            lines.append(f"- [{r.document_title}] p.{r.page_num} ({r.result_type}): {r.snippet[:200]}...")
        return "Local search results:\n" + "\n".join(lines)
    except Exception as e:
        logger.exception("search_local_index failed: %s", e)
        return f"Search error: {e}"


def execute_web_search(
    query: str,
    web_search_fn: Optional[Callable[[str], Any]] = None,
) -> str:
    """Execute web search (Gemini grounding) and return text + sources for the agent."""
    if web_search_fn is None:
        return "Error: web search not configured"
    try:
        result = web_search_fn(query)
        out = result.text or "No response."
        if result.grounding_chunks:
            out += "\n\nSources:\n"
            for i, c in enumerate(result.grounding_chunks[:5], 1):
                out += f"  [{i}] {c.title or 'N/A'}: {c.uri or 'N/A'}\n"
        return out
    except Exception as e:
        logger.exception("web_search failed: %s", e)
        return f"Web search error: {e}"
