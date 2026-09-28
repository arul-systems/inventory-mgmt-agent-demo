from dotenv import load_dotenv
from fastapi import FastAPI
from langchain_core.messages import HumanMessage

load_dotenv()

from agent.agent import agent  # noqa: E402
from api.schemas import ChatRequest, ChatResponse

app = FastAPI(title="Inventory Management Agent")

# uv run uvicorn api.main:app --reload

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Send a user message to the agent and return its final response."""
    config = {"configurable": {"thread_id": request.session_id}}
    state = agent.invoke(
        {"query": request.text, "messages": [HumanMessage(request.text)]},
        config=config,
    )
    return ChatResponse(
        session_id=request.session_id,
        intent=state["route"],
        message=state["summary"],
    )
