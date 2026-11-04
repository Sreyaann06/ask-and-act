import uuid
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from agent.agent import run_agent

app = FastAPI(title="Ask-and-Act Agent")

FRONTEND = Path(__file__).resolve().parent.parent / "frontend" / "index.html"
MAX_MESSAGE_LEN = 2000
MAX_HISTORY_ITEMS = 40

sessions = {}  # session_id -> conversation history (in memory only)


class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str


@app.get("/")
def index():
    return FileResponse(FRONTEND)


@app.post("/chat")
def chat(req: ChatRequest):
    message = (req.message or "").strip()
    if not message:
        return JSONResponse(status_code=400, content={"error": "Message cannot be empty."})
    if len(message) > MAX_MESSAGE_LEN:
        return JSONResponse(
            status_code=400,
            content={"error": f"Message is too long (max {MAX_MESSAGE_LEN} characters)."},
        )

    session_id = req.session_id or str(uuid.uuid4())
    history = sessions.setdefault(session_id, [])
    if len(history) > MAX_HISTORY_ITEMS:
        history.clear()  # simple cap so memory can't grow forever

    try:
        answer, tool_log = run_agent(history, message)
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"error": str(e), "session_id": session_id},
        )

    return {"session_id": session_id, "answer": answer, "tools_used": tool_log}