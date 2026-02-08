"""
Chat route: POST message + optional region context, returns agent reply and sources.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from multimodal_search.api.dependencies import get_agent_runner

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    selected_region_context: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    sources: list


@router.post("", response_model=ChatResponse)
def chat(
    body: ChatRequest,
    agent_runner=Depends(get_agent_runner),
):
    """Send a message to the agent; optionally include selected figure/region context."""
    reply, sources = agent_runner(body.message, body.selected_region_context)
    return ChatResponse(reply=reply, sources=sources)
