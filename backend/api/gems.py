from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from ..deps import get_current_user

router = APIRouter(prefix="/api/v1/gems")

# Gem pack catalog 
PACK_CATALOG = [
    {"id": "starter", "name": "Starter Pack", "gems": 100, "price": 4.99, "currency": "USD"},
    {"id": "standard", "name": "Standard Pack", "gems": 500, "price": 19.99, "currency": "USD"},
    {"id": "premium", "name": "Premium Pack", "gems": 1200, "price": 39.99, "currency": "USD"},
    {"id": "mega", "name": "Mega Pack", "gems": 3000, "price": 79.99, "currency": "USD"},
]

class CheckoutRequest(BaseModel):
    pack_id: str
    payment_provider: str = "stripe"

@router.get("/packs")
def get_gem_packs():
    """Get available gem packs for purchase"""
    return {"packs": PACK_CATALOG}

@router.post("/checkout")
def create_checkout_session(req: CheckoutRequest, user=Depends(get_current_user)):
    """Create a checkout session for gem purchase"""
    pack = next((p for p in PACK_CATALOG if p["id"] == req.pack_id), None)
    if not pack:
        raise HTTPException(status_code=404, detail="Gem pack not found")
    
    # In production, this would integrate with Stripe/payment provider
    # For now, return a mock checkout URL
    checkout_url = f"https://checkout.stripe.com/mock/{req.pack_id}?user_id={user['user_id']}"
    
    return {
        "checkout_session_url": checkout_url,
        "pack": pack,
        "user_id": user["user_id"]
    }

@router.get("/ledger")
def get_gem_ledger(cursor: Optional[str] = None, limit: int = 50, user=Depends(get_current_user)):
    """Get user's gem transaction history"""
    # This would normally query the ledger service
    # For now, return mock data
    return {
        "transactions": [
            {
                "id": "tx_1",
                "type": "purchase",
                "amount": 500,
                "description": "Standard Pack Purchase",
                "timestamp": "2025-01-15T10:30:00Z",
                "balance_after": 500
            },
            {
                "id": "tx_2", 
                "type": "debit",
                "amount": -25,
                "description": "Chat message with Luna",
                "timestamp": "2025-01-15T11:00:00Z",
                "balance_after": 475
            }
        ],
        "next_cursor": None
    }