from typing import Optional

from pydantic import BaseModel, Field

from agent.model.item import Item


class Transfer(BaseModel):
    """A record of an item moving between warehouses, mirroring a row of the `transfers` table."""

    id: int
    item_id: int
    from_location: str
    to_location: str
    quantity: int = Field(description="Units moved (the item's full quantity).")
    status: str
    created_at: str


class TransferResult(BaseModel):
    """Outcome of a successful transfer: the item at its new location and the transfer record."""

    item: Item
    transfer: Transfer


class ItemTransferResponse(BaseModel):
    """Structured response returned by the item transfer agent."""

    message: str = Field(description="Short user-facing confirmation of what was done, or why it could not be done.")
    item: Optional[Item] = Field(
        default=None,
        description="The item at its new location, as returned by the transfer tool. Null if no transfer happened.",
    )
    transfer: Optional[Transfer] = Field(
        default=None,
        description="The transfer record as returned by the transfer tool. Null if no transfer happened.",
    )
