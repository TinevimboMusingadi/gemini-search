"""
SQLite database and schema for documents, pages, text_chunks, regions.
Supports keyword search via FTS5 and stores OCR text, region labels, crop paths.
"""
import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional

from sqlalchemy import (
    Column,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    text,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from multimodal_search.core.config import get_settings

logger = logging.getLogger(__name__)

Base = declarative_base()


class Document(Base):
    """PDF document metadata."""

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_hash = Column(String(64), unique=True, nullable=False, index=True)
    filename = Column(String(512), nullable=False)
    total_pages = Column(Integer, nullable=False)
    # Optional: path where PDF is stored (e.g. under data/pdfs/)
    storage_path = Column(String(1024), nullable=True)


class Page(Base):
    """Single page of a document (rendered image + OCR text)."""

    __tablename__ = "pages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    page_num = Column(Integer, nullable=False)  # 1-based
    image_path = Column(String(1024), nullable=True)  # path to rendered page image
    ocr_text = Column(Text, nullable=True)
    ocr_metadata = Column(Text, nullable=True)  # JSON string of raw Vision response


class TextChunk(Base):
    """Chunk of OCR text for embedding and keyword search."""

    __tablename__ = "text_chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    page_id = Column(Integer, ForeignKey("pages.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)  # order within page
    text = Column(Text, nullable=False)
    # Vector store id for this chunk (e.g. "chunk_123")
    vector_id = Column(String(128), nullable=True, index=True)


class Region(Base):
    """Detected region on a page (figure, table, diagram) with bounding box and label."""

    __tablename__ = "regions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    page_id = Column(Integer, ForeignKey("pages.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    label = Column(String(512), nullable=False)  # from Gemini detection
    box_y0 = Column(Float, nullable=False)
    box_x0 = Column(Float, nullable=False)
    box_y1 = Column(Float, nullable=False)
    box_x1 = Column(Float, nullable=False)
    crop_path = Column(String(1024), nullable=True)
    vector_id = Column(String(128), nullable=True, index=True)


# FTS5 virtual table for full-text search over text_chunks and document titles
# We use a trigger to keep pages_fts in sync with pages.ocr_text for keyword search.
# Alternatively we could create text_chunks_fts; the plan says "keyword over text_chunks and document titles".
# SQLite FTS5: create virtual table that mirrors a content table.
# For simplicity we'll create an FTS5 table over text_chunks.text and link to documents via document_id.
# Schema: we need keyword search over text_chunks and optionally region labels.
# So: one FTS table on text_chunks (content='text_chunks', content_rowid='id') and we search there,
# then join to pages/documents. Or we can have a combined "searchable" table. Easiest: FTS5 on text_chunks.

# FTS5 table creation is done in init_db() with raw SQL because SQLAlchemy doesn't ship FTS5 DDL nicely.


def get_engine(db_path: Optional[Path] = None) -> Engine:
    """Create or return SQLite engine."""
    settings = get_settings()
    path = db_path or settings.resolved_db_path
    path.parent.mkdir(parents=True, exist_ok=True)
    url = f"sqlite:///{path}"
    logger.info("Database engine: %s", url)
    # timeout: seconds to wait when DB is locked (e.g. API holding connection).
    return create_engine(
        url,
        connect_args={"check_same_thread": False, "timeout": 60},
        echo=False,
    )


def init_db(engine: Optional[Engine] = None) -> Engine:
    """Create all tables and FTS5 virtual table. Idempotent."""
    if engine is None:
        engine = get_engine()
    Base.metadata.create_all(engine)

    # WAL mode: allows one writer + multiple readers. Skip if DB is locked (e.g. API running).
    try:
        with engine.connect() as conn:
            conn.execute(text("PRAGMA journal_mode=WAL"))
            conn.commit()
    except Exception as e:
        if "locked" in str(e).lower() or "busy" in str(e).lower():
            logger.warning(
                "Could not set WAL mode (database locked). Stop the API and run indexer alone to avoid lock."
            )
        else:
            raise

    # FTS5 for keyword search on text_chunks
    try:
        with engine.connect() as conn:
            conn.execute(text(
                """CREATE VIRTUAL TABLE IF NOT EXISTS text_chunks_fts USING fts5(
                text, content='text_chunks', content_rowid='id'
            )"""
            ))
            conn.execute(text(
                """CREATE TRIGGER IF NOT EXISTS text_chunks_ai AFTER INSERT ON text_chunks BEGIN
                INSERT INTO text_chunks_fts(rowid, text) VALUES (new.id, new.text);
            END"""
            ))
            conn.execute(text(
                """CREATE TRIGGER IF NOT EXISTS text_chunks_ad AFTER DELETE ON text_chunks BEGIN
                INSERT INTO text_chunks_fts(text_chunks_fts, rowid, text) VALUES ('delete', old.id, old.text);
            END"""
            ))
            conn.execute(text(
                """CREATE TRIGGER IF NOT EXISTS text_chunks_au AFTER UPDATE ON text_chunks BEGIN
                INSERT INTO text_chunks_fts(text_chunks_fts, rowid, text) VALUES ('delete', old.id, old.text);
                INSERT INTO text_chunks_fts(rowid, text) VALUES (new.id, new.text);
            END"""
            ))
            conn.commit()
    except Exception as e:
        if "locked" in str(e).lower() or "busy" in str(e).lower():
            raise RuntimeError(
                "Database is locked (the API is probably running). Stop uvicorn, then run the indexer again."
            ) from e
        raise

    logger.info("Database and FTS5 initialized")
    return engine


_session_factory: Optional[sessionmaker] = None


def get_session_factory(engine: Optional[Engine] = None) -> sessionmaker:
    global _session_factory
    if _session_factory is None:
        eng = engine or get_engine()
        _session_factory = sessionmaker(autocommit=False, autoflush=False, bind=eng)
        logger.debug("Session factory created")
    return _session_factory


@contextmanager
def get_db_session(engine: Optional[Engine] = None) -> Generator[Session, None, None]:
    """Yield a DB session; commit on success, rollback on exception."""
    factory = get_session_factory(engine)
    session = factory()
    try:
        yield session
        session.commit()
    except Exception as e:
        logger.exception("Database session error: %s", e)
        session.rollback()
        raise
    finally:
        session.close()
