from functools import lru_cache

from langchain_openai import ChatOpenAI

from agent.model import AgentState

SYSTEM_PROMPT = """You are the final summarizer for an inventory management system. You are given the outcome of an action taken by a specialist agent and must write one clear, concise message for the end user.

For now you will only ever be given information about a single inventory item (or no item, if the action failed, was rejected, or found nothing). Use the item's fields (SKU, name, quantity, reorder threshold, location) and the agent's message to describe what happened, in plain language. If there is no item, just relay the agent's message.

Do not invent facts beyond what is given to you."""


@lru_cache(maxsize=1)
def _get_llm():
    return ChatOpenAI(model="gpt-4o-mini", temperature=0)


def summarizer(state: AgentState) -> AgentState:
    """Summarize the specialist agent's item result into a final user-facing message."""
    item = state.get("item")
    result = state.get("result")
    message = getattr(result, "message", None)

    context = (
        f"Agent message: {message}\n"
        f"Item: {item.model_dump_json() if item is not None else None}"
    )
    response = _get_llm().invoke(
        [("system", SYSTEM_PROMPT), ("user", context)]
    )
    return {"summary": response.content}
