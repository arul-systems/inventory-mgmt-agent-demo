from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Incoming request to the chat endpoint."""

    session_id: str = Field(description="Identifies the conversation; reused across turns.")
    text: str = Field(description="The end user's message.")


class ChatResponse(BaseModel):
    """Final, user-facing response for a chat turn."""

    session_id: str
    message: str
