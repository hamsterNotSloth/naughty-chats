from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from ..deps import get_current_user

router = APIRouter(prefix="/api/v1")

class UserProfile(BaseModel):
    username: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    birth_year: Optional[int] = None

class Session(BaseModel):
    id: str
    device: str
    location: str
    last_active: str
    current: bool

class NotificationItem(BaseModel):
    id: str
    type: str
    title: str
    message: str
    timestamp: str
    read: bool

class ReportRequest(BaseModel):
    target_type: str  # "character", "message", "image", "user"
    target_id: str
    reason_code: str
    details: Optional[str] = None

class StatusResponse(BaseModel):
    incidents: List[dict] = []
    degraded_services: List[str] = []

# Mock data storage
USER_PROFILES = {}
USER_SESSIONS = {}
NOTIFICATIONS = {}
REPORTS = []
SYSTEM_STATUS = {"incidents": [], "degraded_services": []}

@router.get("/me")
def get_current_user_profile(user=Depends(get_current_user)):
    """Get current user's profile information"""
    user_id = user["user_id"]
    
    if user_id not in USER_PROFILES:
        USER_PROFILES[user_id] = {
            "username": user.get("username", f"user_{user_id}"),
            "bio": None,
            "avatar_url": None,
            "birth_year": None,
            "created_at": "2025-01-15T10:00:00Z"
        }
    
    return USER_PROFILES[user_id]

@router.patch("/me/profile")
def update_user_profile(profile: UserProfile, user=Depends(get_current_user)):
    """Update current user's profile"""
    user_id = user["user_id"]
    
    if user_id not in USER_PROFILES:
        USER_PROFILES[user_id] = {}
    
    # Update fields
    for field, value in profile.dict(exclude_unset=True).items():
        USER_PROFILES[user_id][field] = value
    
    return USER_PROFILES[user_id]

@router.get("/users/{username}/public")
def get_public_user_profile(username: str):
    """Get public view of a user's profile"""
    # In a real implementation, this would query the database
    # For now, return mock data
    return {
        "username": username,
        "bio": "AI character enthusiast",
        "avatar_url": f"https://api.dicebear.com/7.x/avataaars/svg?seed={username}",
        "created_at": "2025-01-10T08:00:00Z",
        "character_count": 5,
        "total_chats": 120
    }

@router.get("/me/sessions")
def get_user_sessions(user=Depends(get_current_user)):
    """Get user's active sessions"""
    user_id = user["user_id"]
    
    if user_id not in USER_SESSIONS:
        USER_SESSIONS[user_id] = [
            {
                "id": "sess_current",
                "device": "Chrome on Windows",
                "location": "New York, US",
                "last_active": "2025-01-15T12:00:00Z",
                "current": True
            }
        ]
    
    return {"sessions": USER_SESSIONS[user_id]}

@router.delete("/me/sessions/{session_id}")
def revoke_user_session(session_id: str, user=Depends(get_current_user)):
    """Revoke a user session"""
    user_id = user["user_id"]
    
    if user_id in USER_SESSIONS:
        USER_SESSIONS[user_id] = [
            s for s in USER_SESSIONS[user_id] 
            if s["id"] != session_id
        ]
    
    return {"ok": True}

@router.get("/notifications")
def get_notifications(cursor: Optional[str] = None, user=Depends(get_current_user)):
    """Get user's notifications"""
    user_id = user["user_id"]
    
    if user_id not in NOTIFICATIONS:
        NOTIFICATIONS[user_id] = [
            {
                "id": "notif_1",
                "type": "generation_complete",
                "title": "Image Generation Complete",
                "message": "Your image generation for Luna is ready!",
                "timestamp": "2025-01-15T11:30:00Z",
                "read": False
            }
        ]
    
    return {"notifications": NOTIFICATIONS[user_id], "next_cursor": None}

@router.post("/report")
def submit_report(report: ReportRequest, user=Depends(get_current_user)):
    """Submit a content report"""
    report_id = f"report_{len(REPORTS) + 1}"
    
    report_data = {
        "id": report_id,
        "reporter_id": user["user_id"],
        "target_type": report.target_type,
        "target_id": report.target_id,
        "reason_code": report.reason_code,
        "details": report.details,
        "timestamp": "2025-01-15T12:00:00Z",
        "status": "pending"
    }
    
    REPORTS.append(report_data)
    
    return {"report_id": report_id, "status": "submitted"}

@router.get("/status")
def get_system_status():
    """Get system status and incidents"""
    return SYSTEM_STATUS

@router.post("/onboarding/complete")
def complete_onboarding(user=Depends(get_current_user)):
    """Mark user onboarding as complete"""
    user_id = user["user_id"]
    
    # In a real implementation, this would update the user's onboarding status
    return {"status": "completed", "user_id": user_id}

@router.get("/tags")
def get_available_tags():
    """Get list of available character tags"""
    return {
        "tags": [
            {"name": "anime", "count": 150},
            {"name": "fantasy", "count": 120},
            {"name": "sci-fi", "count": 80},
            {"name": "romance", "count": 200},
            {"name": "adventure", "count": 95},
            {"name": "mystery", "count": 60},
            {"name": "comedy", "count": 75},
            {"name": "drama", "count": 110}
        ]
    }