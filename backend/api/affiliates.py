from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from ..deps import get_current_user

router = APIRouter(prefix="/api/v1/affiliates")

class AffiliateStats(BaseModel):
    referral_code: str
    clicks: int
    signups: int
    purchases: int
    commission_pending: float
    commission_paid: float

class RequestAffiliateStatus(BaseModel):
    reason: Optional[str] = None

# Mock affiliate data storage
AFFILIATE_DATA = {}

@router.get("/me")
def get_affiliate_stats(user=Depends(get_current_user)):
    """Get user's affiliate statistics"""
    user_id = user["user_id"]
    
    # Generate a referral code based on user ID if not exists
    if user_id not in AFFILIATE_DATA:
        AFFILIATE_DATA[user_id] = {
            "referral_code": f"REF_{user_id.upper()[:8]}",
            "clicks": 0,
            "signups": 0,
            "purchases": 0,
            "commission_pending": 0.0,
            "commission_paid": 0.0,
            "status": "active"
        }
    
    return AFFILIATE_DATA[user_id]

@router.post("/request")
def request_affiliate_access(req: RequestAffiliateStatus, user=Depends(get_current_user)):
    """Request affiliate program access (if gated)"""
    user_id = user["user_id"]
    
    # Auto-approve for now (in production this might require manual review)
    if user_id not in AFFILIATE_DATA:
        AFFILIATE_DATA[user_id] = {
            "referral_code": f"REF_{user_id.upper()[:8]}",
            "clicks": 0,
            "signups": 0,
            "purchases": 0,
            "commission_pending": 0.0,
            "commission_paid": 0.0,
            "status": "approved"
        }
    
    return {"status": "approved"}

@router.get("/leaderboard")
def get_affiliate_leaderboard(limit: int = 10):
    """Get top affiliates (public leaderboard)"""
    # Sort by total commission earned
    sorted_affiliates = sorted(
        AFFILIATE_DATA.values(),
        key=lambda x: x["commission_paid"] + x["commission_pending"],
        reverse=True
    )[:limit]
    
    # Remove sensitive data for public view
    public_data = []
    for i, affiliate in enumerate(sorted_affiliates):
        public_data.append({
            "rank": i + 1,
            "referral_code": affiliate["referral_code"][:3] + "***",  # Partially hide code
            "total_signups": affiliate["signups"],
            "total_earnings": affiliate["commission_paid"] + affiliate["commission_pending"]
        })
    
    return {"leaderboard": public_data}