from functools import lru_cache

from langchain_aws import ChatBedrockConverse

from agent.model import AgentState, IntentClassification
from agent.nodes.context import messages_with_summary

SYSTEM_PROMPT = """You route requests for an inventory management system. Given the conversation, choose the specialist that should handle the user's latest message:
- inv_mgmt_agent: create, look up, update, or delete a single inventory item.
- item_transfer_agent: move items between locations/warehouses. Handle list fo warehouses.
- vendor_agent: cut purchase orders (POs) with vendors, and procure/receive ordered items into inventory.
Use earlier messages to resolve references such as "it" or "that item"."""


@lru_cache(maxsize=1)
def _get_classifier():
    return ChatBedrockConverse(model="us.anthropic.claude-sonnet-4-5-20250929-v1:0", region_name="us-east-2", temperature=0).with_structured_output(
        IntentClassification
    )


def planner(state: AgentState) -> AgentState:
    """Classify the user's intent from the conversation and route to the matching specialist node."""
    classification = _get_classifier().invoke(
        [("system", SYSTEM_PROMPT), *messages_with_summary(state)]
    )
    return {"route": classification.intent}
