"""
SQLite database for persistent agent memory (chat history).
Isolated from the main search index DB.
"""
import logging
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Generator, Optional

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
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


class ChatSession(Base):
    """A conversation session."""

    __tablename__ = "chat_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ChatMessage(Base):
    """A single message in a chat session."""

    __tablename__ = "chat_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(
        String(36),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role = Column(String(20), nullable=False)  # user, model, tool
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)


def get_memory_engine(db_path: Optional[Path] = None) -> Engine:
    """Create or return SQLite engine for chat memory."""
    settings = get_settings()
    # Use a separate DB file for memory, e.g., chat_history.db in the same dir
    if db_path:
        path = db_path
    else:
        # Default to chat_history.db next to the main db
        main_db = settings.resolved_db_path
        path = main_db.parent / "chat_history.db"

    path.parent.mkdir(parents=True, exist_ok=True)
    url = f"sqlite:///{path}"
    logger.debug("Memory DB engine: %s", url)
    
    return create_engine(
        url,
        connect_args={"check_same_thread": False, "timeout": 30},
        echo=False,
    )


def init_memory_db(engine: Optional[Engine] = None) -> Engine:
    """Create tables for chat memory."""
    if engine is None:
        engine = get_memory_engine()
    Base.metadata.create_all(engine)
    
    # Enable WAL mode for better concurrency
    try:
        with engine.connect() as conn:
            conn.execute(text("PRAGMA journal_mode=WAL"))
            conn.commit()
    except Exception as e:
        logger.warning("Could not set WAL mode for memory DB: %s", e)
        
    return engine


_memory_session_factory: Optional[sessionmaker] = None


def get_memory_session_factory(engine: Optional[Engine] = None) -> sessionmaker:
    global _memory_session_factory
    if _memory_session_factory is None:
        eng = engine or get_memory_engine()
        init_memory_db(eng)  # Ensure tables exist
        _memory_session_factory = sessionmaker(autocommit=False, autoflush=False, bind=eng)
    return _memory_session_factory


@contextmanager
def get_memory_session() -> Generator[Session, None, None]:
    """Yield a memory DB session."""
    factory = get_memory_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception as e:
        logger.exception("Memory DB session error: %s", e)
        session.rollback()
        raise
    finally:
        session.close()
