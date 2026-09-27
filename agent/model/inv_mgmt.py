from typing import Optional

from pydantic import BaseModel, Field

from agent.model.item import Item


class InvMgmtResponse(BaseModel):
    """Structured response returned by the inventory management agent."""

    message: str = Field(description="Short user-facing confirmation of what was done, or why it could not be done.")
    item: Optional[Item] = Field(
        default=None,
        description="The item as returned by the tools (created, found, updated, or deleted). Null if no item was affected or found.",
    )
