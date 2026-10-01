from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from agent.model import AgentState, Intent
from agent.nodes.planner import planner
from agent.nodes.compactor import compactor
from agent.nodes.inv_mgmt_agent import inv_mgmt_agent
from agent.nodes.item_transfer_agent import item_transfer_agent
from agent.nodes.vendor_agent import vendor_agent
from agent.nodes.summarizer import summarizer


def route_after_planner(state: AgentState) -> Intent:
    """Send the request to the specialist node chosen by the planner."""
    return state.get("route", Intent.INV_MGMT_AGENT)


def build_graph() -> CompiledStateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("planner", planner)
    graph.add_node("compactor", compactor)
    graph.add_node(Intent.INV_MGMT_AGENT.value, inv_mgmt_agent)
    graph.add_node(Intent.ITEM_TRANSFER_AGENT.value, item_transfer_agent)
    graph.add_node(Intent.VENDOR_AGENT.value, vendor_agent)
    graph.add_node("summarizer", summarizer)

    graph.add_edge(START, "planner")
    graph.add_edge(START, "compactor")
    graph.add_conditional_edges(
        "planner",
        route_after_planner,
        {
            Intent.INV_MGMT_AGENT: Intent.INV_MGMT_AGENT.value,
            Intent.ITEM_TRANSFER_AGENT: Intent.ITEM_TRANSFER_AGENT.value,
            Intent.VENDOR_AGENT: Intent.VENDOR_AGENT.value,
        },
    )

    graph.add_edge(Intent.INV_MGMT_AGENT.value, "summarizer")
    graph.add_edge(Intent.ITEM_TRANSFER_AGENT.value, "summarizer")
    graph.add_edge(Intent.VENDOR_AGENT.value, "summarizer")
    graph.add_edge("summarizer", END)
    graph.add_edge("compactor", END)

    serde = JsonPlusSerializer(
        allowed_msgpack_modules=[
            ("agent.model.intent", "Intent"),
            ("agent.model.item", "Item"),
            ("agent.model.inv_mgmt", "InvMgmtResponse"),
            ("agent.model.transfer", "ItemTransferResponse"),
            ("agent.model.transfer", "Transfer"),
            ("agent.model.purchase_order", "VendorResponse"),
            ("agent.model.purchase_order", "PurchaseOrder"),
        ]
    )
    return graph.compile(checkpointer=InMemorySaver(serde=serde))


agent = build_graph()
