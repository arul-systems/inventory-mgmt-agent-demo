from typing import Any

from agent.model import AgentState


def messages_with_summary(state: AgentState) -> list[Any]:
    """Conversation messages for an LLM call, prefixed with the summary of any compacted history."""
    conversation_summary = state.get("conversation_summary")
    if not conversation_summary:
        return list(state["messages"])
    return [
        ("system", f"Summary of the earlier conversation: {conversation_summary}"),
        *state["messages"],
    ]
