#!/usr/bin/env python3
"""
Inspect the search DB: tables, row counts, and sample rows for every field.

Run from project root: uv run python scripts/inspect_db.py
Use this to verify index contents and to improve the search engine or DB structure.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure src is on path when run as script
_root = Path(__file__).resolve().parents[1]
if str(_root / "src") not in sys.path:
    sys.path.insert(0, str(_root / "src"))

from sqlalchemy import text

from multimodal_search.core.config import get_settings
from multimodal_search.core.database import (
    Base,
    Document,
    Page,
    Region,
    TextChunk,
    get_engine,
    init_db,
)


def main() -> None:
    settings = get_settings()
    db_path = settings.resolved_db_path
    print(f"Database path: {db_path}")
    print(f"Exists: {db_path.exists()}")
    if not db_path.exists():
        print("No database file yet. Run the indexer first (e.g. run-index).")
        return

    engine = get_engine()
    init_db(engine)

    with engine.connect() as conn:
        # List all tables (including FTS5 virtual table)
        r = conn.execute(
            text(
                "SELECT name FROM sqlite_master WHERE type IN ('table','view') "
                "ORDER BY name"
            )
        )
        tables = [row[0] for row in r.fetchall()]
    print(f"\nTables: {tables}")

    # ORM tables and sample size
    orm_tables = [
        (Document, "documents", 5),
        (Page, "pages", 5),
        (TextChunk, "text_chunks", 5),
        (Region, "regions", 5),
    ]

    counts = []
    for model, label, sample_size in orm_tables:
        with engine.connect() as conn:
            count = conn.execute(text(f"SELECT COUNT(*) FROM {label}")).scalar()
        counts.append(count)
        print(f"\n--- {label} (count={count}) ---")
        if count == 0:
            continue
        # Get column names from model
        cols = [c.key for c in model.__table__.columns]
        print(f"Columns: {cols}")
        with engine.connect() as conn:
            rows = conn.execute(
                text(f"SELECT * FROM {label} LIMIT {sample_size}")
            ).fetchall()
        for i, row in enumerate(rows):
            print(f"  Row {i + 1}:")
            for j, col in enumerate(cols):
                val = row[j]
                if isinstance(val, str) and len(val) > 80:
                    val = val[:77] + "..."
                print(f"    {col}: {val!r}")

    # FTS5 virtual table (row count only; content lives in text_chunks)
    if "text_chunks_fts" in tables:
        with engine.connect() as conn:
            fts_count = conn.execute(
                text("SELECT COUNT(*) FROM text_chunks_fts")
            ).scalar()
        print(f"\n--- text_chunks_fts (count={fts_count}) ---")
        print("FTS5 virtual table; content linked to text_chunks. No sample dump.")

    if sum(counts) == 0:
        print("\nAll main tables are empty. Run the indexer (e.g. run-index) to populate.")
    print("\nDone.")


if __name__ == "__main__":
    main()
