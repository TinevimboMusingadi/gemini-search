"""
Agent orchestration: Gemini with SearchDB and WebSearch tools.
Loop: user message -> Gemini -> if function_calls execute tools -> append results -> Gemini again.
"""
import logging
from pathlib import Path
from typing import Any, List, Optional

from google import genai
from google.genai import types
from sqlalchemy.orm import Session

from multimodal_search.agent.tools.search_tools import (
    execute_search_local,
    execute_web_search,
    get_search_tool_declarations,
)
from multimodal_search.core.memory_db import ChatMessage, ChatSession, get_memory_session
from multimodal_search.services.gemini_client import get_gemini_client
from multimodal_search.services.web_search import web_search

logger = logging.getLogger(__name__)

MAX_AGENT_STEPS = 10
DEFAULT_MODEL = "gemini-3-pro-preview"


def _load_system_prompt() -> str:
    p = Path(__file__).resolve().parent / "prompts" / "system.txt"
    if p.exists():
        return p.read_text(encoding="utf-8").strip()
    return "You are a helpful assistant with access to local PDF search and web search. Cite your sources."


def _load_history(session_id: str, limit: int = 20) -> List[types.Content]:
    """Load chat history from memory DB."""
    history = []
    with get_memory_session() as session:
        # Check if session exists
        chat_session = session.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not chat_session:
            return []
        
        messages = (
            session.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.timestamp.asc())
            .limit(limit)
            .all()
        )
        
        for msg in messages:
            # Map DB roles to Gemini roles
            role = "user" if msg.role == "user" else "model"
            # Note: Tool outputs are tricky to persist perfectly in simple schema, 
            # so we simplify to user/model text for context.
            # Ideally we'd store full structured content.
            history.append(types.Content(role=role, parts=[types.Part(text=msg.content)]))
            
    return history


def _save_message(session_id: str, role: str, content: str):
    """Save a message to memory DB."""
    with get_memory_session() as session:
        # Ensure session exists (create if not, though API should handle this)
        chat_session = session.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not chat_session:
            chat_session = ChatSession(id=session_id, title="New Chat")
            session.add(chat_session)
            session.flush()
            
        msg = ChatMessage(session_id=session_id, role=role, content=content)
        session.add(msg)


def run_agent(
    message: str,
    *,
    session: Any, # Main DB session for search
    search_engine_fn: Any,
    selected_region_context: Optional[str] = None,
    client: Optional[genai.Client] = None,
    model: str = DEFAULT_MODEL,
    session_id: Optional[str] = None,
) -> tuple[str, List[dict]]:
    """
    Run the agent: user message + optional region context, tools = SearchDB + WebSearch.
    Returns (final_reply_text, list of source dicts for UI).
    """
    if client is None:
        client = get_gemini_client()
    system_instruction = _load_system_prompt()
    tools = get_search_tool_declarations()

    # Load history if session_id provided
    history = []
    if session_id:
        history = _load_history(session_id)

    user_content = message
    if selected_region_context:
        user_content = f"Context (selected figure/region): {selected_region_context}\n\nUser question: {message}"

    # Add current user message to history for the API call
    history.append(types.Content(role="user", parts=[types.Part(text=user_content)]))
    
    # Save user message to DB
    if session_id:
        _save_message(session_id, "user", user_content)

    sources = []
    step = 0

    while step < MAX_AGENT_STEPS:
        step += 1
        logger.debug("Agent step %s", step)
        try:
            # Gemini 3 Pro config with thinking
            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                tools=tools,
                thinking_config=types.ThinkingConfig(thinking_level="high") if "gemini-3" in model else None,
                temperature=1.0 if "gemini-3" in model else None, # Default 1.0 for Gemini 3
            )
            
            response = client.models.generate_content(
                model=model,
                contents=history,
                config=config,
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
            reply_text = response.text or ""
            # Save model reply
            if session_id:
                _save_message(session_id, "model", reply_text)
            return reply_text, sources

        # Append model response to history (it contains the function call)
        history.append(content)

        # Execute each function call and append tool response
        for fc in function_calls:
            name = getattr(fc, "name", None) or ""
            args = getattr(fc, "args", None) or {}
            logger.info("Agent tool call: %s %s", name, args)
            
            result_str = ""
            if name == "search_local_index":
                q = args.get("query", "")
                k = args.get("top_k", 10)
                m = args.get("mode", "hybrid")
                result_str = execute_search_local(q, top_k=k, mode=m, search_fn=search_engine_fn)
                sources.append({"type": "local", "query": q, "mode": m, "summary": result_str[:300]})
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
    final_text = response.text or "Stopped after max steps."
    if session_id:
        _save_message(session_id, "model", final_text)
    return final_text, sources
