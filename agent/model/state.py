from typing import Annotated, Any, Optional, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

from agent.model.intent import Intent
from agent.model.item import Item


class AgentState(TypedDict):
    """Shared state passed between all nodes in the graph."""

    messages: Annotated[list[AnyMessage], add_messages]
    query: str
    route: Optional[Intent]
    item: Optional[Item]
    result: Optional[Any]
    summary: Optional[str]
    conversation_summary: Optional[str]
