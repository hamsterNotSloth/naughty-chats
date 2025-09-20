from fastapi import APIRouter, Depends
from pydantic import BaseModel
from ..deps import get_current_user
from uuid import uuid4

router = APIRouter(prefix="/api/v1/chat")


class SessionReq(BaseModel):
    character_id: str


class MessageReq(BaseModel):
    content: str


SESSIONS = {}


@router.post("/sessions")
def create_session(req: SessionReq, user=Depends(get_current_user)):
    sid = f"sess:{uuid4().hex}"
    SESSIONS[sid] = {"id": sid, "character_id": req.character_id, "user_id": user["user_id"], "created_at": None}
    return {"session_id": sid}


@router.post("/sessions/{session_id}/message")
def send_message(session_id: str, req: MessageReq, user=Depends(get_current_user)):
    # placeholder: in production this enqueues or streams tokens
    # return a simple ack + estimated cost
    estimate = max(1, len(req.content) // 50)
    return {"status": "accepted", "estimated_cost": estimate, "note": "stream via WS in real implementation"}
