from typing import Optional

from pydantic import BaseModel, Field


class Item(BaseModel):
    """An inventory item, mirroring a row of the `items` table."""

    id: Optional[int] = Field(default=None, description="Database id; assigned on creation.")
    sku: str = Field(description="Unique SKU identifying the item.")
    name: str = Field(description="Human-readable item name.")
    quantity: int = Field(ge=0, description="Units currently in stock.")
    reorder_threshold: int = Field(ge=0, description="Stock level at which the item should be reordered.")
    location: Optional[str] = Field(default=None, description="Warehouse/location holding the item.")
    vendor_id: Optional[int] = Field(default=None, description="Id of the vendor supplying the item.")
