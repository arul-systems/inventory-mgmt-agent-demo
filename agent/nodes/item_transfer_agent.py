from functools import lru_cache
from typing import Union

from langchain.agents import create_agent
from langchain_aws import ChatBedrockConverse
from langchain_core.tools import tool

from agent.db.database import list_locations, transfer_item
from agent.model import AgentState, Item, ItemTransferResponse, Transfer, TransferResult
from agent.nodes.context import messages_with_summary


@tool
def list_warehouses() -> list[str]:
    """List all known warehouses/locations."""
    return list_locations()


@tool
def transfer_inventory_item(sku: str, to_location: str) -> Union[TransferResult, dict]:
    """Move a whole inventory item, identified by SKU, to another warehouse and record the transfer."""
    try:
        result = transfer_item(sku, to_location)
    except ValueError as e:
        return {"error": str(e)}
    return TransferResult(item=Item(**result["item"]), transfer=Transfer(**result["transfer"]))


TOOLS = [list_warehouses, transfer_inventory_item]

SYSTEM_PROMPT = """You are an item transfer assistant for an inventory management system. You move a single inventory item from its current warehouse to another warehouse using the tools provided.

Guidelines:
- Items are identified by their SKU and the destination is a warehouse name. If either is missing, ask the user for it rather than guessing.
- Before transferring, call list_warehouses and make sure the destination is an existing warehouse. If it is not, do not transfer; tell the user which warehouses exist.
- Transfers always move the whole item (all of its units). If the user asks to move only some units, explain that partial transfers are not supported.
- Never make up data; only report what the tools return. If a tool returns an error, explain it to the user plainly instead of retrying blindly.
- If the request involves more than one item, handle only one and tell the user you can move a single item at a time."""


@lru_cache(maxsize=1)
def _get_agent():
    llm = ChatBedrockConverse(model="us.anthropic.claude-sonnet-4-5-20250929-v1:0", region_name="us-east-2", temperature=0)
    return create_agent(
        llm, TOOLS, system_prompt=SYSTEM_PROMPT, response_format=ItemTransferResponse
    )


def item_transfer_agent(state: AgentState) -> AgentState:
    """Move a single inventory item between warehouses based on the user's request."""
    response = _get_agent().invoke({"messages": messages_with_summary(state)})
    structured: ItemTransferResponse = response["structured_response"]
    return {"item": structured.item, "result": structured}
