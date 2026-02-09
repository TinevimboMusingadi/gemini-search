#!/usr/bin/env python3
"""
Test the Agent Memory (Chat History) and Session Management.

Run:
  python scripts/test_agent_memory.py
"""
import logging
import sys
import uuid
from pathlib import Path

# Ensure src is on path
_root = Path(__file__).resolve().parents[1]
if str(_root / "src") not in sys.path:
    sys.path.insert(0, str(_root / "src"))

from multimodal_search.core.memory_db import (
    ChatMessage,
    ChatSession,
    get_memory_session,
    init_memory_db,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("test_memory")


def test_memory_db():
    """Test creating sessions and messages."""
    logger.info("Initializing memory DB...")
    init_memory_db()

    session_id = str(uuid.uuid4())
    logger.info("Creating session: %s", session_id)

    with get_memory_session() as session:
        # Create Session
        chat_session = ChatSession(id=session_id, title="Test Session")
        session.add(chat_session)
        session.flush()

        # Add User Message
        msg1 = ChatMessage(
            session_id=session_id,
            role="user",
            content="Hello, can you find info on transformers?",
        )
        session.add(msg1)
        
        # Add Model Message
        msg2 = ChatMessage(
            session_id=session_id,
            role="model",
            content="Sure, I can help with that. Searching local index...",
        )
        session.add(msg2)
        
    logger.info("Session and messages saved.")

    # Verify
    with get_memory_session() as session:
        saved_session = session.query(ChatSession).filter(ChatSession.id == session_id).first()
        if saved_session:
            logger.info("Verified Session: %s (Title: %s)", saved_session.id, saved_session.title)
        else:
            logger.error("Session NOT found!")

        messages = (
            session.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.timestamp.asc())
            .all()
        )
        logger.info("Found %d messages:", len(messages))
        for m in messages:
            logger.info("  [%s] %s", m.role, m.content)

    logger.info("Memory DB test complete.")


if __name__ == "__main__":
    test_memory_db()
