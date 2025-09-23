from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional
from ..deps import get_current_user

router = APIRouter(prefix="/api/v1/characters")

CHAR_STORE = {}

class CharacterCreateReq(BaseModel):
    name: str
    short_description: str = ""
    tags: List[str] = []
    nsfw_flags: Optional[List[str]] = []
    personality: Optional[str] = ""
    example_dialogues: Optional[List[str]] = []

class CharacterSummary(BaseModel):
    id: str
    name: str
    avatar_url: Optional[str]
    short_description: str
    tags: List[str]
    rating_avg: float
    rating_count: int
    gem_cost_per_message: Optional[int]
    nsfw_flags: List[str]
    last_active: str

@router.get("")
def list_characters(
    sort: str = Query("popular", description="Sort by: popular, trending, new, recent"),
    limit: int = Query(50, le=100),
    filter: Optional[str] = Query(None, description="Filter criteria"),
    q: Optional[str] = Query(None, description="Search query"),
    cursor: Optional[str] = None
):
    """List characters with filtering and sorting"""
    
    # Apply search filter if provided
    items = list(CHAR_STORE.values())
    
    if q:
        items = [char for char in items if q.lower() in char["name"].lower() or q.lower() in char.get("short_description", "").lower()]
    
    # Apply sorting
    if sort == "popular":
        items = sorted(items, key=lambda x: x.get("rating_count", 0), reverse=True)
    elif sort == "trending":
        items = sorted(items, key=lambda x: x.get("last_active", ""), reverse=True)
    elif sort == "new":
        items = sorted(items, key=lambda x: x.get("created_at", ""), reverse=True)
    
    # Apply limit
    items = items[:limit]
    
    # Convert to summary format
    summaries = []
    for char in items:
        summaries.append({
            "id": char["id"],
            "name": char["name"],
            "avatar_url": f"https://api.dicebear.com/7.x/avataaars/svg?seed={char['name']}",
            "short_description": char.get("short_description", ""),
            "tags": char.get("tags", []),
            "rating_avg": 4.2,  # Mock rating
            "rating_count": 156,  # Mock count
            "gem_cost_per_message": 5,
            "nsfw_flags": char.get("nsfw_flags", []),
            "last_active": "2025-01-15T12:00:00Z"
        })
    
    return {
        "items": summaries,
        "next_cursor": None if len(summaries) < limit else "next_page_token"
    }

@router.post("")
def create_character(req: CharacterCreateReq, user=Depends(get_current_user)):
    """Create a new character"""
    cid = f"char:{len(CHAR_STORE) + 1}"
    
    obj = {
        "id": cid,
        "name": req.name,
        "short_description": req.short_description,
        "tags": req.tags,
        "nsfw_flags": req.nsfw_flags or [],
        "personality": req.personality or "",
        "example_dialogues": req.example_dialogues or [],
        "author_id": user["user_id"],
        "created_at": "2025-01-15T12:00:00Z",
        "published": False
    }
    
    CHAR_STORE[cid] = obj
    return {"id": cid}

@router.get("/{character_id}")
def get_character(character_id: str):
    """Get detailed character information"""
    char = CHAR_STORE.get(character_id)
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Return full character details
    return {
        **char,
        "avatar_url": f"https://api.dicebear.com/7.x/avataaars/svg?seed={char['name']}",
        "rating_avg": 4.2,
        "rating_count": 156,
        "gem_cost_per_message": 5,
        "gallery": [],  # Mock empty gallery
        "stats": {
            "total_chats": 1250,
            "total_messages": 15600,
            "favorite_count": 89
        }
    }

@router.patch("/{character_id}/steps")
def update_character_step(character_id: str, step_data: dict, user=Depends(get_current_user)):
    """Update character creation step data"""
    char = CHAR_STORE.get(character_id)
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
    
    if char["author_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Update character with step data
    char.update(step_data)
    CHAR_STORE[character_id] = char
    
    return {"status": "updated"}

@router.post("/{character_id}/favorite")
def toggle_favorite(character_id: str, user=Depends(get_current_user)):
    """Add/remove character from favorites"""
    char = CHAR_STORE.get(character_id)
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # In a real implementation, this would update the user's favorites list
    return {"favorited": True}

@router.post("/{character_id}/publish")
def publish_character(character_id: str, user=Depends(get_current_user)):
    """Publish or unpublish a character"""
    char = CHAR_STORE.get(character_id)
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
    
    if char["author_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    char["published"] = not char.get("published", False)
    CHAR_STORE[character_id] = char
    
    return {"published": char["published"]}
