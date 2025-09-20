from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from ..deps import get_current_user

router = APIRouter(prefix="/api/v1/characters")

CHAR_STORE = {}


class CharacterCreateReq(BaseModel):
    name: str
    short_description: str = ""
    tags: List[str] = []


@router.get("")
def list_characters(limit: int = 50):
    # naive projection
    items = list(CHAR_STORE.values())[:limit]
    return {"items": items}


@router.post("")
def create_character(req: CharacterCreateReq, user=Depends(get_current_user)):
    cid = f"char:{len(CHAR_STORE) + 1}"
    obj = {"id": cid, "name": req.name, "short_description": req.short_description, "tags": req.tags, "author_id": user["user_id"]}
    CHAR_STORE[cid] = obj
    return obj
