from typing import Any, List, Optional, TypedDict

from agent.model.intent import Intent
from agent.model.item import Item


class AgentState(TypedDict):
    """Shared state passed between all nodes in the graph."""

    messages: List[Any]
    query: str
    route: Optional[Intent]
    item: Optional[Item]
    result: Optional[Any]
    summary: Optional[str]
