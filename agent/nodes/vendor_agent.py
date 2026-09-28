from functools import lru_cache
from typing import Optional, Union

from langchain.agents import create_agent
from langchain_aws import ChatBedrockConverse
from langchain_core.tools import tool

from agent.db import database
from agent.model import AgentState, Item, PurchaseOrder, PurchaseOrderResult, VendorResponse
from agent.nodes.context import messages_with_summary


def _to_result(row: dict) -> PurchaseOrderResult:
    return PurchaseOrderResult(
        item=Item(**row["item"]), purchase_order=PurchaseOrder(**row["purchase_order"])
    )


@tool
def create_purchase_order(sku: str, quantity: int) -> Union[PurchaseOrderResult, dict]:
    """Cut a purchase order (PO) for a quantity of an item, identified by SKU, with the item's assigned vendor."""
    try:
        return _to_result(database.create_purchase_order(sku, quantity))
    except ValueError as e:
        return {"error": str(e)}


@tool
def receive_purchase_order(po_id: int) -> Union[PurchaseOrderResult, dict]:
    """Procure a purchase order: mark it received and add its ordered quantity to the item's inventory."""
    try:
        return _to_result(database.receive_purchase_order(po_id))
    except ValueError as e:
        return {"error": str(e)}


@tool
def list_purchase_orders(sku: Optional[str] = None, status: Optional[str] = None) -> list[PurchaseOrder]:
    """List purchase orders, optionally filtered by item SKU and/or status ('ordered' or 'received')."""
    return [PurchaseOrder(**row) for row in database.list_purchase_orders(sku, status)]


TOOLS = [create_purchase_order, receive_purchase_order, list_purchase_orders]

SYSTEM_PROMPT = """You are a procurement assistant for an inventory management system. You cut purchase orders (POs) for a single inventory item with its assigned vendor, and you procure (receive) POs, which adds the ordered quantity to the item's inventory. Use the tools provided.

Guidelines:
- To cut a PO you need the item's SKU and a quantity greater than zero. If either is missing, ask the user for it and do NOT call any tool yet; never assume or default a quantity (for example, do not assume 1). The PO goes to the item's assigned vendor; you cannot choose a different vendor.
- To procure, you need the PO id. If the user gives an item SKU instead, call list_purchase_orders with that SKU and status 'ordered': receive it if there is exactly one, ask the user which one if there are several, and tell them there is nothing to procure if there are none.
- A PO can only be procured once. Only say inventory was increased if receive_purchase_order succeeded.
- You MUST call a tool before stating that a PO was created, received, or found. Never make up data; only report what the tools return. If a tool returns an error, explain it to the user plainly instead of retrying blindly.
- Handle one item or one PO at a time; if the user asks for several, do only one and say so.
- Keep your final message short and confirm exactly what was done. Set `item` and `purchase_order` exactly as the tools returned them, or null if there is none."""


@lru_cache(maxsize=1)
def _get_agent():
    llm = ChatBedrockConverse(model="us.anthropic.claude-sonnet-4-5-20250929-v1:0", region_name="us-east-2", temperature=0)
    return create_agent(
        llm, TOOLS, system_prompt=SYSTEM_PROMPT, response_format=VendorResponse
    )


def vendor_agent(state: AgentState) -> AgentState:
    """Cut purchase orders and procure items into inventory based on the user's request."""
    response = _get_agent().invoke({"messages": messages_with_summary(state)})
    structured: VendorResponse = response["structured_response"]
    return {"item": structured.item, "result": structured}
