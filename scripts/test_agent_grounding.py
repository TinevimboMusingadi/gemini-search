#!/usr/bin/env python3
"""
Test the Agent's Grounding capabilities (Local DB + Web Search).

Run:
  python scripts/test_agent_grounding.py
"""
import logging
import sys
import uuid
from pathlib import Path

# Ensure src is on path
_root = Path(__file__).resolve().parents[1]
if str(_root / "src") not in sys.path:
    sys.path.insert(0, str(_root / "src"))

from multimodal_search.api.dependencies import get_agent_runner
from multimodal_search.core.database import get_engine, init_db, get_session_factory
from multimodal_search.core.memory_db import init_memory_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("test_agent")


def test_agent_grounding():
    """Ask agent questions to verify tool usage."""
    logger.info("Initializing DBs...")
    
    # Init Main DB (for search)
    engine = get_engine()
    init_db(engine)
    session_factory = get_session_factory(engine)
    main_session = session_factory()
    
    # Init Memory DB (for chat)
    init_memory_db()

    # Get Agent Runner (manually constructed dependencies)
    # We need the search_engine_fn
    from multimodal_search.search.engine import search as search_engine_fn
    
    # Wrapper for search engine to match dependency signature
    def search_fn_wrapper(req):
        return search_engine_fn(main_session, req)

    from multimodal_search.agent.chains import run_agent

    session_id = str(uuid.uuid4())
    logger.info("Session ID: %s", session_id)

    # 1. Test Local Grounding (PDF Context)
    print("\n" + "="*50)
    print("TEST 1: Local PDF Grounding")
    print("="*50)
    q1 = "What is the MAZ Newsletter about? Summarize the key topics."
    print(f"User: {q1}")
    
    reply1, sources1 = run_agent(
        message=q1,
        session=main_session,
        search_engine_fn=search_fn_wrapper,
        session_id=session_id
    )
    print(f"\nAgent: {reply1}\n")
    print("Sources used:")
    for s in sources1:
        print(f" - [{s['type']}] {s.get('query', '')} (Summary: {s.get('summary', '')[:50]}...)")

    # 2. Test Web Grounding (Real-world info)
    print("\n" + "="*50)
    print("TEST 2: Web Search Grounding")
    print("="*50)
    q2 = "Who won the Super Bowl in 2024? What was the score?"
    print(f"User: {q2}")
    
    reply2, sources2 = run_agent(
        message=q2,
        session=main_session,
        search_engine_fn=search_fn_wrapper,
        session_id=session_id
    )
    print(f"\nAgent: {reply2}\n")
    print("Sources used:")
    for s in sources2:
        print(f" - [{s['type']}] {s.get('query', '')} (Summary: {s.get('summary', '')[:50]}...)")

    main_session.close()


if __name__ == "__main__":
    test_agent_grounding()
