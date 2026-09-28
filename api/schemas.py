from pydantic import BaseModel, Field

from agent.model import Intent


class ChatRequest(BaseModel):
    """Incoming request to the chat endpoint."""

    session_id: str = Field(description="Identifies the conversation; reused across turns.")
    text: str = Field(description="The end user's message.")


class ChatResponse(BaseModel):
    """Final, user-facing response for a chat turn."""

    session_id: str
    intent: Intent = Field(description="The intent the planner identified and routed this message to.")
    message: str
