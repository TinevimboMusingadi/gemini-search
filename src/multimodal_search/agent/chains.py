"""
Agent orchestration: Gemini with SearchDB and WebSearch tools.
Loop: user message -> Gemini -> if function_calls execute tools -> append results -> Gemini again.
"""
import logging
from pathlib import Path
from typing import Any, List, Optional

from google import genai
from google.genai import types

from multimodal_search.agent.tools.search_tools import (
    execute_search_local,
    execute_web_search,
    get_search_tool_declarations,
)
from multimodal_search.services.gemini_client import get_gemini_client
from multimodal_search.services.web_search import web_search

logger = logging.getLogger(__name__)

MAX_AGENT_STEPS = 10
DEFAULT_MODEL = "gemini-2.0-flash"


def _load_system_prompt() -> str:
    p = Path(__file__).resolve().parent / "prompts" / "system.txt"
    if p.exists():
        return p.read_text(encoding="utf-8").strip()
    return "You are a helpful assistant with access to local PDF search and web search. Cite your sources."


def run_agent(
    message: str,
    *,
    session: Any,
    search_engine_fn: Any,
    selected_region_context: Optional[str] = None,
    client: Optional[genai.Client] = None,
    model: str = DEFAULT_MODEL,
) -> tuple[str, List[dict]]:
    """
    Run the agent: user message + optional region context, tools = SearchDB + WebSearch.
    Returns (final_reply_text, list of source dicts for UI).
    """
    if client is None:
        client = get_gemini_client()
    system_instruction = _load_system_prompt()
    tools = get_search_tool_declarations()

    user_content = message
    if selected_region_context:
        user_content = f"Context (selected figure/region): {selected_region_context}\n\nUser question: {message}"

    history = [types.Content(role="user", parts=[types.Part(text=user_content)])]
    sources = []
    step = 0

    while step < MAX_AGENT_STEPS:
        step += 1
        logger.debug("Agent step %s", step)
        try:
            response = client.models.generate_content(
                model=model,
                contents=history,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    tools=tools,
                ),
            )
        except Exception as e:
            logger.exception("Agent Gemini call failed: %s", e)
            return f"Error: {e}", sources

        if not response.candidates:
            return "No response from model.", sources

        cand = response.candidates[0]
        content = cand.content
        if not content or not content.parts:
            return (response.text or "No response."), sources

        # Check for function calls
        function_calls = getattr(response, "function_calls", None) or []
        if not function_calls:
            return (response.text or ""), sources

        # Append model response to history
        history.append(content)

        # Execute each function call and append tool response
        for fc in function_calls:
            name = getattr(fc, "name", None) or ""
            args = getattr(fc, "args", None) or {}
            logger.info("Agent tool call: %s %s", name, args)
            if name == "search_local_index":
                q = args.get("query", "")
                k = args.get("top_k", 10)
                result_str = execute_search_local(q, top_k=k, search_fn=search_engine_fn)
                sources.append({"type": "local", "query": q, "summary": result_str[:300]})
            elif name == "web_search":
                q = args.get("query", "")
                result_str = execute_web_search(q, web_search_fn=web_search)
                sources.append({"type": "web", "query": q, "summary": result_str[:300]})
            else:
                result_str = f"Unknown tool: {name}"

            history.append(
                types.Content(
                    role="tool",
                    parts=[types.Part.from_function_response(name=name, response={"result": result_str})],
                )
            )

    logger.warning("Agent hit max steps %s", MAX_AGENT_STEPS)
    return (response.text or "Stopped after max steps."), sources
