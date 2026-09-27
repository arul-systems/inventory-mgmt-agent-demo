from enum import Enum

from pydantic import BaseModel, Field


class Intent(str, Enum):
    """The specialist node that should handle a given user request."""

    INV_MGMT_AGENT = "inv_mgmt_agent"
    ITEM_TRANSFER_AGENT = "item_transfer_agent"
    VENDOR_AGENT = "vendor_agent"


class IntentClassification(BaseModel):
    """Structured output produced by the planner to classify user intent."""

    intent: Intent = Field(
        description="The specialist agent best suited to handle the user's request."
    )
