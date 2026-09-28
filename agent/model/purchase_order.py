from typing import Optional

from pydantic import BaseModel, Field

from agent.model.item import Item


class PurchaseOrder(BaseModel):
    """A purchase order (PO) with a vendor, mirroring a row of `purchase_orders` plus item/vendor names."""

    id: int
    item_id: int
    sku: str
    vendor_id: int
    vendor_name: str
    quantity: int = Field(description="Units ordered.")
    status: str = Field(description="'ordered' until procured, then 'received'.")
    created_at: str
    received_at: Optional[str] = None


class PurchaseOrderResult(BaseModel):
    """Outcome of creating or receiving a PO: the item (with current stock) and the purchase order."""

    item: Item
    purchase_order: PurchaseOrder


class VendorResponse(BaseModel):
    """Structured response returned by the vendor agent."""

    message: str = Field(description="Short user-facing confirmation of what was done, or why it could not be done.")
    item: Optional[Item] = Field(
        default=None,
        description="The item as returned by the tools (with updated quantity after a PO is received). Null if none.",
    )
    purchase_order: Optional[PurchaseOrder] = Field(
        default=None,
        description="The purchase order as returned by the tools. Null if no PO was created or received.",
    )
