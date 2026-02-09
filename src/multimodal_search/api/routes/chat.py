"""
Chat route: POST message + optional region context, returns agent reply and sources.
Supports persistent sessions via chat_history.db.
"""
import logging
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from multimodal_search.api.dependencies import get_agent_runner
from multimodal_search.core.memory_db import ChatMessage, ChatSession, get_memory_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    selected_region_context: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    sources: list


class CreateSessionResponse(BaseModel):
    session_id: str
    title: str


class MessageSchema(BaseModel):
    role: str
    content: str
    timestamp: str


class SessionHistoryResponse(BaseModel):
    session_id: str
    messages: List[MessageSchema]


class SessionListItem(BaseModel):
    session_id: str
    title: Optional[str]
    created_at: str


@router.get("/sessions", response_model=List[SessionListItem])
def list_sessions():
    """List all chat sessions."""
    with get_memory_session() as session:
        sessions = (
            session.query(ChatSession)
            .order_by(ChatSession.created_at.desc())
            .all()
        )
        return [
            SessionListItem(
                session_id=s.id,
                title=s.title,
                created_at=s.created_at.isoformat() if s.created_at else "",
            )
            for s in sessions
        ]


@router.post("/sessions", response_model=CreateSessionResponse)
def create_session():
    """Start a new chat session."""
    session_id = str(uuid.uuid4())
    with get_memory_session() as session:
        chat_session = ChatSession(id=session_id, title="New Chat")
        session.add(chat_session)
    return CreateSessionResponse(session_id=session_id, title="New Chat")


@router.get("/sessions/{session_id}", response_model=SessionHistoryResponse)
def get_session_history(session_id: str):
    """Retrieve chat history for a session."""
    with get_memory_session() as session:
        chat_session = session.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not chat_session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        messages = (
            session.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.timestamp.asc())
            .all()
        )
        
        return SessionHistoryResponse(
            session_id=session_id,
            messages=[
                MessageSchema(
                    role=m.role,
                    content=m.content,
                    timestamp=m.timestamp.isoformat()
                ) for m in messages
            ]
        )


@router.post("/{session_id}", response_model=ChatResponse)
def chat_with_session(
    session_id: str,
    body: ChatRequest,
    agent_runner=Depends(get_agent_runner),
):
    """Send a message to the agent within a specific session."""
    # Verify session exists
    with get_memory_session() as session:
        if not session.query(ChatSession).filter(ChatSession.id == session_id).first():
             raise HTTPException(status_code=404, detail="Session not found")

    reply, sources = agent_runner(
        message=body.message,
        selected_region_context=body.selected_region_context,
        session_id=session_id
    )
    return ChatResponse(reply=reply, sources=sources)


@router.post("", response_model=ChatResponse)
def chat_stateless(
    body: ChatRequest,
    agent_runner=Depends(get_agent_runner),
):
    """Legacy stateless chat (creates a temporary session or runs without one)."""
    # For backward compatibility, we can run without session_id or create a temp one.
    # Let's run without session_id (no memory persistence) for now, or we could auto-create.
    # Given the plan emphasizes memory, let's just run it. The agent handles session_id=None gracefully.
    reply, sources = agent_runner(body.message, body.selected_region_context)
    return ChatResponse(reply=reply, sources=sources)
