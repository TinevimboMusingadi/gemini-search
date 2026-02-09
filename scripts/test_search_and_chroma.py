#!/usr/bin/env python3
"""
Test the Search API and Inspect ChromaDB.

Run:
  uv run python scripts/test_search_and_chroma.py

This script:
1. Inspects ChromaDB to verify vectors are stored.
2. Runs sample searches via the Search Engine (internal call, not HTTP) to test:
   - Keyword Search
   - Semantic (Vector) Search
   - Hybrid Search
"""
import logging
import sys
from pathlib import Path

# Ensure src is on path
_root = Path(__file__).resolve().parents[1]
if str(_root / "src") not in sys.path:
    sys.path.insert(0, str(_root / "src"))

from multimodal_search.core.config import get_settings
from multimodal_search.core.database import get_engine, init_db, get_session_factory
from multimodal_search.core.schemas.search import SearchRequest
from multimodal_search.core.vector_store import get_vector_store, ChromaVectorStore
from multimodal_search.search.engine import search

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("test_search")


def inspect_chroma():
    """Check ChromaDB collection stats and sample a few items."""
    print("\n--- Inspecting ChromaDB ---")
    vec_store = get_vector_store()
    
    if not isinstance(vec_store, ChromaVectorStore):
        print("Vector store is NOT ChromaDB (is it InMemory?). Check config.")
        return

    coll = vec_store._collection
    count = coll.count()
    print(f"Collection '{coll.name}' count: {count}")
    
    if count > 0:
        # Peek at first 3 items
        peek = coll.peek(limit=3)
        ids = peek.get("ids", [])
        metas = peek.get("metadatas", [])
        print(f"Sample IDs: {ids}")
        print(f"Sample Metadata: {metas}")
    else:
        print("ChromaDB is empty! Did reindex_embeddings.py finish?")


def test_search_modes(query: str):
    """Run search in all 3 modes."""
    print(f"\n--- Testing Search (Query: '{query}') ---")
    
    engine = get_engine()
    init_db(engine)
    session_factory = get_session_factory(engine)
    session = session_factory()

    try:
        # 1. Keyword Only
        print("\n[Mode: KEYWORD]")
        req = SearchRequest(query=query, top_k=3, mode="keyword")
        resp = search(session, req)
        if not resp.results:
            print("  No results.")
        for i, r in enumerate(resp.results):
            print(f"  {i+1}. [{r.score:.4f}] {r.document_title} (Page {r.page_num}) - {r.result_type}")
            print(f"     Snippet: {r.snippet[:100]}...")

        # 2. Semantic Only
        print("\n[Mode: SEMANTIC]")
        req = SearchRequest(query=query, top_k=3, mode="semantic")
        resp = search(session, req)
        if not resp.results:
            print("  No results.")
        for i, r in enumerate(resp.results):
            print(f"  {i+1}. [{r.score:.4f}] {r.document_title} (Page {r.page_num}) - {r.result_type}")
            print(f"     Snippet: {r.snippet[:100]}...")

        # 3. Hybrid
        print("\n[Mode: HYBRID]")
        req = SearchRequest(query=query, top_k=3, mode="hybrid")
        resp = search(session, req)
        if not resp.results:
            print("  No results.")
        for i, r in enumerate(resp.results):
            print(f"  {i+1}. [{r.score:.4f}] {r.document_title} (Page {r.page_num}) - {r.result_type}")
            print(f"     Snippet: {r.snippet[:100]}...")

    finally:
        session.close()


def main():
    # 1. Check Chroma
    inspect_chroma()

    # 2. Run Search Tests
    # Pick a query relevant to your PDF content (from logs: "Manifold", "Newsletter", "Zimbabwe")
    test_search_modes("Zimbabwe marketing newsletter")
    test_search_modes("Manifold Constrained Hyper Connections")


if __name__ == "__main__":
    main()
