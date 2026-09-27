import sqlite3
from functools import lru_cache
from typing import Optional, Union

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from agent.db.database import create_item, delete_item, get_item, update_item
from agent.model import AgentState, InvMgmtResponse, Item


@tool
def create_inventory_item(item: Item) -> Union[Item, dict]:
    """Create a new inventory item. Fails if an item with this SKU already exists."""
    try:
        return Item(**create_item(**item.model_dump(exclude={"id"})))
    except sqlite3.IntegrityError:
        return {"error": f"An item with sku '{item.sku}' already exists."}


@tool
def get_inventory_item(sku: str) -> Union[Item, dict]:
    """Look up a single inventory item by SKU."""
    row = get_item(sku)
    return Item(**row) if row else {"error": f"No item found with sku '{sku}'."}


@tool
def update_inventory_item(
    sku: str,
    name: Optional[str] = None,
    quantity: Optional[int] = None,
    reorder_threshold: Optional[int] = None,
    location: Optional[str] = None,
    vendor_id: Optional[int] = None,
) -> Union[Item, dict]:
    """Update one or more fields of an existing inventory item identified by SKU."""
    row = update_item(
        sku=sku,
        name=name,
        quantity=quantity,
        reorder_threshold=reorder_threshold,
        location=location,
        vendor_id=vendor_id,
    )
    return Item(**row) if row else {"error": f"No item found with sku '{sku}'."}


@tool
def delete_inventory_item(sku: str) -> Union[Item, dict]:
    """Delete a single inventory item by SKU. Returns the item that was deleted."""
    row = get_item(sku)
    if row is None:
        return {"error": f"No item found with sku '{sku}'."}
    delete_item(sku)
    return Item(**row)


TOOLS = [create_inventory_item, get_inventory_item, update_inventory_item, delete_inventory_item]

SYSTEM_PROMPT = """You are an inventory management assistant. You manage inventory items in a database, one item at a time, using the tools provided.

Guidelines:
- Items are identified by their SKU. If the user refers to an item without a SKU, ask for it rather than guessing.
- Use the tools to create, look up, update, or delete an item. Never make up item data; only report what the tools return.
- For updates, only change the fields the user asked to change. To create an item you need at least a SKU, name, quantity, and reorder threshold; ask for any that are missing.
- If a tool returns an error, explain it to the user plainly instead of retrying blindly.
- If the request involves more than one item, handle only one and tell the user you can act on a single item at a time.
- Keep your final message short and confirm exactly what was done. Set `item` to the item exactly as the tools returned it, or null if there is none."""


@lru_cache(maxsize=1)
def _get_agent():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    return create_react_agent(
        llm, TOOLS, prompt=SYSTEM_PROMPT, response_format=InvMgmtResponse
    )


def inv_mgmt_agent(state: AgentState) -> AgentState:
    """Perform CRUD on a single inventory item based on the user's query."""
    response = _get_agent().invoke({"messages": [("user", state["query"])]})
    structured: InvMgmtResponse = response["structured_response"]
    return {"item": structured.item, "result": structured}
