import base64
import json

from langchain_core.messages import HumanMessage

from agent.agent import agent
from agent.db.database import init_db, seed_db

# Runs once per cold start, outside the handler; both are no-ops if already initialised.
# INVENTORY_DB_PATH (set in Terraform) points the database at /tmp, the only writable path.
init_db()
seed_db()


def _response(status: int, body: dict) -> dict:
    return {
        "statusCode": status,
        "headers": {"content-type": "application/json"},
        "body": json.dumps(body),
    }


def handler(event, context):
    """Lambda function URL entry point: expects a JSON body with `session_id` and `text`."""
    raw = event.get("body") or ""
    if event.get("isBase64Encoded"):
        raw = base64.b64decode(raw).decode("utf-8")
    try:
        payload = json.loads(raw)
        session_id, text = payload["session_id"], payload["text"]
        if not isinstance(session_id, str) or not isinstance(text, str):
            raise TypeError
    except (json.JSONDecodeError, KeyError, TypeError):
        return _response(400, {"error": "Body must be JSON with string fields 'session_id' and 'text'."})

    state = agent.invoke(
        {"query": text, "messages": [HumanMessage(text)]},
        config={"configurable": {"thread_id": session_id}},
    )
    return _response(
        200,
        {"session_id": session_id, "intent": state["route"].value, "message": state["summary"]},
    )
