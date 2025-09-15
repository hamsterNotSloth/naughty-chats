from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from passlib.context import CryptContext
from datetime import datetime
import os
import logging
from dotenv import load_dotenv

import cosmos  # changed from relative import to absolute to work when run as a top-level module
from entra_auth import entra_dependency
from anyio import to_thread

load_dotenv()

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("naughty-chats")

APP_VERSION = "0.1.0"
app = FastAPI(title="Naughty Chats API", version=APP_VERSION)

# Dynamic CORS origins via env var
allowed_origins_env = os.getenv("ALLOWED_ORIGINS")
if allowed_origins_env:
    origins_list = [o.strip() for o in allowed_origins_env.split(',') if o.strip()]
else:
    origins_list = ["http://localhost:3000"]  # default for local dev

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Pydantic models
class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(BaseModel):  # retained for possible future self-service profile creation (not used now)
    email: EmailStr
    password: str  # UNUSED with Entra (placeholder for compatibility)
    agreeTerms: bool

class User(UserBase):
    id: str
    gemBalance: int
    isActive: bool

class Token(BaseModel):  # deprecated; keep for backward compatibility if frontend still expects shape (will be removed)
    access_token: str
    token_type: str
    user: User
    gemBalance: int

class CharacterSummary(BaseModel):
    id: str
    name: str
    avatarUrl: str
    shortDescription: str
    tags: List[str]
    ratingAvg: float
    ratingCount: int
    gemCostPerMessage: Optional[int] = None
    nsfwFlags: bool
    lastActive: str

class CharacterListResponse(BaseModel):
    items: List[CharacterSummary]
    nextCursor: Optional[str] = None

# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

async def get_current_user(authorization: Optional[str] = Header(None)):  # expects 'Authorization' header
    claims = await entra_dependency(authorization)
    # Prefer 'preferred_username' or 'upn' or 'email' claim for user identity
    username = claims.get('preferred_username') or claims.get('upn') or claims.get('email') or claims.get('oid')
    if not username:
        raise HTTPException(status_code=401, detail="No usable identity claim in token")
    # Ensure user exists (auto-provision pattern). Password unused with Entra.
    user_obj = await to_thread.run_sync(cosmos.get_user_by_username, username)
    if user_obj is None:
        # Try email claim
        email_claim = claims.get('email') or username
        # Create placeholder hashed password (not used); reuse existing helper
        hashed_password = get_password_hash(os.urandom(8).hex())
        try:
            user_obj = await to_thread.run_sync(lambda: cosmos.create_user(username=username, email=email_claim, hashed_password=hashed_password))
        except ValueError:
            # Race: created by another request; fetch again
            user_obj = await to_thread.run_sync(cosmos.get_user_by_username, username)
    return user_obj

# API Endpoints
@app.get("/")
async def root():
    return {"message": "Naughty Chats API", "version": APP_VERSION}

@app.get("/healthz")
async def healthz():
    return {"status": "ok", "version": APP_VERSION}

# Removed legacy /api/auth/register and /api/auth/login endpoints (Entra handles auth). Frontend should obtain access token via MSAL and call protected endpoints with Authorization header.

@app.get("/api/characters", response_model=CharacterListResponse)
async def get_characters(sort: str = "popular", limit: int = 12):
    try:
        chars = await to_thread.run_sync(cosmos.list_characters, sort, limit)
    except Exception as e:  # surface cosmos errors
        logger.exception("Cosmos query failed for /api/characters")
        raise HTTPException(status_code=500, detail=f"Cosmos query failed: {e}")
    if not chars:
        logger.error("No character data present in Cosmos DB (characters container empty)")
        raise HTTPException(status_code=500, detail="No character data available in Cosmos DB")
    items = [
        CharacterSummary(
            id=c.get('id',''),
            name=c.get('name',''),
            avatarUrl=c.get('avatar_url','') or "",
            shortDescription=c.get('short_description','') or "",
            tags=c.get('tags',[]) or [],
            ratingAvg=c.get('rating_avg',0.0),
            ratingCount=c.get('rating_count',0),
            gemCostPerMessage=c.get('gem_cost_per_message'),
            nsfwFlags=c.get('nsfw_flags', False),
            lastActive=str(c.get('last_active',''))
        ) for c in chars
    ]
    return CharacterListResponse(items=items, nextCursor=None)

@app.get("/api/me")
async def get_current_user_info(current_user = Depends(get_current_user)):
    return User(
        id=current_user['id'],
        email=current_user['email'],
        username=current_user['username'],
        gemBalance=current_user['gem_balance'],
        isActive=current_user['is_active'],
    )

@app.on_event("startup")
async def on_startup():
    # Fail fast if cosmos unreachable
    if not cosmos.health_check():
        logger.critical("Cosmos DB connectivity failed during startup")
        raise RuntimeError("Cosmos DB connectivity failed during startup")
    logger.info("Startup complete: Cosmos reachable")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)