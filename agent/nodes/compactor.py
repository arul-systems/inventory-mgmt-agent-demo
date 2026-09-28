import logging
from functools import lru_cache

from langchain_core.messages import HumanMessage, RemoveMessage
from langchain_core.messages.utils import count_tokens_approximately, trim_messages
from langchain_openai import ChatOpenAI

from agent.model import AgentState

logger = logging.getLogger(__name__)

MAX_TOKENS = 300


@lru_cache(maxsize=1)
def _get_llm():
    return ChatOpenAI(model="gpt-4o-mini", temperature=0)


def _generate_summary(state: AgentState, removed_messages: list) -> str:
    """Fold the messages being removed into the running conversation summary."""
    conversation_summary = state.get("conversation_summary")
    if conversation_summary:
        instruction = (
            f"This is a summary of the conversation to date: {conversation_summary}\n\n"
            "Extend the summary by taking into account the new messages above:"
        )
    else:
        instruction = "Create a summary of the conversation above:"
    return _get_llm().invoke([*removed_messages, HumanMessage(instruction)]).content


def compactor(state: AgentState) -> AgentState:
    """Trim old messages to a token budget and fold what was removed into conversation_summary."""
    trimmed = trim_messages(
        state["messages"],
        strategy="last",
        token_counter=count_tokens_approximately,
        max_tokens=MAX_TOKENS,
        start_on="human",
        end_on=("human", "tool"),
    )
    kept_ids = {m.id for m in trimmed}
    removed = [m for m in state["messages"] if m.id not in kept_ids]
    if not removed:
        return {}

    logger.info("Removing %d messages and updating conversation summary.", len(removed))
    return {
        "conversation_summary": _generate_summary(state, removed),
        "messages": [RemoveMessage(id=m.id) for m in removed],
    }
