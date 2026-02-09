#!/usr/bin/env python3
"""
Interactive Agent Chat CLI.
Chat with Gemini 3 Pro, which has access to your Local DB (Search) and the Web.

Run:
  python scripts/chat_cli.py
"""
import sys
import uuid
import logging
from pathlib import Path

# Ensure src is on path
_root = Path(__file__).resolve().parents[1]
if str(_root / "src") not in sys.path:
    sys.path.insert(0, str(_root / "src"))

from multimodal_search.core.database import get_engine, init_db, get_session_factory
from multimodal_search.core.memory_db import init_memory_db
from multimodal_search.agent.chains import run_agent
from multimodal_search.search.engine import search as search_engine_fn

# Configure logging to show Agent "thought" process
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s", # Simple format for CLI
    handlers=[logging.StreamHandler(sys.stdout)]
)
# Silence internal noisy loggers
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
logging.getLogger("multimodal_search.core.vector_store").setLevel(logging.ERROR)

def search_fn_wrapper(session):
    """Closure to pass session to search engine."""
    return lambda req: search_engine_fn(session, req)

def main():
    print("="*60)
    print("Gemini 3 Pro Agent - Interactive Chat")
    print("="*60)
    print("Initializing Agent & Memory...")
    
    # Init DBs
    engine = get_engine()
    init_db(engine)
    session_factory = get_session_factory(engine)
    main_session = session_factory()
    init_memory_db()

    session_id = str(uuid.uuid4())
    print(f"Session ID: {session_id}")
    print("Ready! The Agent can search your PDFs and the Web.")
    print("(Type 'exit', 'quit', or 'clear' to start new session)\n")

    while True:
        try:
            user_input = input("\nYou > ").strip()
            if user_input.lower() in ("exit", "quit"):
                break
            if user_input.lower() == "clear":
                session_id = str(uuid.uuid4())
                print(f"--- New Session: {session_id} ---")
                continue
            if not user_input:
                continue

            print("\nAgent is thinking...")
            
            # Run Agent
            reply, sources = run_agent(
                message=user_input,
                session=main_session,
                search_engine_fn=search_fn_wrapper(main_session),
                session_id=session_id
            )
            
            print(f"\nAgent > {reply}\n")
            
            if sources:
                print("Sources used:")
                for s in sources:
                    sType = s.get('type', 'unknown')
                    sQuery = s.get('query', 'N/A')
                    print(f" - [{sType}] {sQuery}")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

    main_session.close()
    print("\nGoodbye!")

if __name__ == "__main__":
    main()
