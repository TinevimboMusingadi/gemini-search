#!/usr/bin/env python3
"""
Interactive Search CLI for the Local Database.
Uses Keyword Search (FTS5) by default as Vector Search is currently unavailable.

Run:
  python scripts/search_cli.py
"""
import sys
import logging
from pathlib import Path
from typing import List

# Ensure src is on path
_root = Path(__file__).resolve().parents[1]
if str(_root / "src") not in sys.path:
    sys.path.insert(0, str(_root / "src"))

from multimodal_search.core.database import get_engine, init_db, get_session_factory
from multimodal_search.core.schemas.search import SearchRequest
from multimodal_search.search.engine import search

# Configure logging (less verbose for CLI)
logging.basicConfig(level=logging.WARNING)

def print_results(results: List[any]):
    if not results:
        print("\n  No results found.")
        return

    print(f"\n  Found {len(results)} results:")
    for i, r in enumerate(results):
        print(f"\n  {i+1}. {r.document_title} (Page {r.page_num})")
        print(f"     Type: {r.result_type} | Score: {r.score:.4f}")
        print(f"     Snippet: {r.snippet.replace(chr(10), ' ')[:150]}...")

def main():
    print("="*60)
    print("Gemini Search CLI - Local Database")
    print("="*60)
    print("Initializing Database...")
    
    engine = get_engine()
    init_db(engine)
    session_factory = get_session_factory(engine)
    session = session_factory()
    
    print("Ready! (Type 'exit' or 'quit' to stop)\n")

    while True:
        try:
            query = input("Search Query > ").strip()
            if query.lower() in ("exit", "quit"):
                break
            if not query:
                continue

            # Default to keyword since Chroma is down
            req = SearchRequest(query=query, top_k=5, mode="keyword")
            
            print(f"Searching for: '{query}'...")
            resp = search(session, req)
            print_results(resp.results)
            print("-" * 60)

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

    session.close()
    print("\nGoodbye!")

if __name__ == "__main__":
    main()
