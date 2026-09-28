from functools import lru_cache

from langchain_aws import ChatBedrockConverse
from langchain_core.messages import AIMessage

from agent.model import AgentState
from agent.nodes.context import messages_with_summary

SYSTEM_PROMPT = """You are the final summarizer for an inventory management system. You are given the conversation so far and the outcome of the action a specialist agent just took for the user's latest message. Write one clear, concise reply to that latest message.

For now you will only ever be given information about a single inventory item, which may be null. Use the item's fields (SKU, name, quantity, reorder threshold, location) and the agent's message to describe what happened, in plain language. A null item does not mean the action failed: the agent's message is the source of truth about whether it succeeded, so relay it faithfully.

Use the conversation for context, but do not invent facts beyond what is given to you."""


@lru_cache(maxsize=1)
def _get_llm():
    return ChatBedrockConverse(model="us.anthropic.claude-sonnet-4-5-20250929-v1:0", region_name="us-east-2", temperature=0)


def summarizer(state: AgentState) -> AgentState:
    """Summarize the specialist agent's item result into a final user-facing message."""
    item = state.get("item")
    result = state.get("result")
    message = getattr(result, "message", None)

    outcome = (
        f"Agent message: {message}\n"
        f"Item: {item.model_dump_json() if item is not None else None}"
    )
    response = _get_llm().invoke(
        [("system", SYSTEM_PROMPT), *messages_with_summary(state), ("system", outcome)]
    )
    return {"summary": response.content, "messages": [AIMessage(response.content)]}
