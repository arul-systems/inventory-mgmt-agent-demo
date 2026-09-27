from functools import lru_cache

from langchain_openai import ChatOpenAI

from agent.model import AgentState, IntentClassification


@lru_cache(maxsize=1)
def _get_classifier():
    return ChatOpenAI(model="gpt-4o-mini", temperature=0).with_structured_output(
        IntentClassification
    )


def planner(state: AgentState) -> AgentState:
    """Classify the user's query intent and route to the matching specialist node."""
    classification = _get_classifier().invoke(state["query"])
    return {"route": classification.intent}
