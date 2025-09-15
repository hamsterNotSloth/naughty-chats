from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

import cosmos  # changed from relative import to absolute to work when run as a top-level module
from anyio import to_thread

load_dotenv()

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

# Security / Auth (legacy local JWT fallback; Entra ID validation to be added)
SECRET_KEY = os.getenv("SECRET_KEY") or ("dev-secret" if os.getenv("LOCAL_AUTH_ENABLED", "true").lower() == "true" else None)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

if SECRET_KEY is None:
    # Fail fast in production if missing
    raise RuntimeError("SECRET_KEY not set and LOCAL_AUTH_ENABLED is false. Configure SECRET_KEY or enable local auth.")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Pydantic models
class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    agreeTerms: bool

class UserLogin(BaseModel):
    identifier: str  # email or username
    password: str

class User(UserBase):
    id: str
    gemBalance: int
    isActive: bool

class Token(BaseModel):
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

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user_obj = await to_thread.run_sync(cosmos.get_user_by_username, username)
    if user_obj is None:
        raise credentials_exception
    return user_obj

# API Endpoints
@app.get("/")
async def root():
    return {"message": "Naughty Chats API", "version": APP_VERSION}

@app.get("/healthz")
async def healthz():
    return {"status": "ok", "version": APP_VERSION}

@app.post("/api/auth/register", response_model=Token)
async def register(user: UserCreate):
    # Validate terms agreement
    if not user.agreeTerms:
        raise HTTPException(status_code=400, detail="Must agree to terms and conditions")

    # Derive a base username from email local part and ensure uniqueness
    base_username = user.email.split('@')[0]
    candidate = base_username
    suffix = 1
    # Loop until unique in Cosmos
    while await to_thread.run_sync(cosmos.get_user_by_username, candidate) is not None:
        candidate = f"{base_username}{suffix}"
        suffix += 1

    # Check email uniqueness
    existing_email = await to_thread.run_sync(cosmos.get_user_by_email, user.email)
    if existing_email:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    hashed_password = get_password_hash(user.password)
    try:
        user_obj = await to_thread.run_sync(cosmos.create_user, email=user.email, username=candidate, hashed_password=hashed_password)
    except ValueError:
        raise HTTPException(status_code=400, detail="User already exists")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": candidate}, expires_delta=access_token_expires)

    user_response = User(
        id=user_obj['id'],
        email=user_obj['email'],
        username=user_obj['username'],
        gemBalance=user_obj['gem_balance'],
        isActive=user_obj['is_active']
    )
    return {"access_token": access_token, "token_type": "bearer", "user": user_response, "gemBalance": user_obj['gem_balance']}

@app.post("/api/auth/login", response_model=Token)
async def login(user_credentials: UserLogin):
    user_obj = await to_thread.run_sync(cosmos.get_user_by_username, user_credentials.identifier)
    if user_obj is None:
        user_obj = await to_thread.run_sync(cosmos.get_user_by_email, user_credentials.identifier)
    if user_obj is None or not verify_password(user_credentials.password, user_obj['hashed_password']):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user_obj.username}, expires_delta=access_token_expires)
    user_response = User(id=user_obj['id'], email=user_obj['email'], username=user_obj['username'], gemBalance=user_obj['gem_balance'], isActive=user_obj['is_active'])
    return {"access_token": access_token, "token_type": "bearer", "user": user_response, "gemBalance": user_obj['gem_balance']}

@app.get("/api/characters", response_model=CharacterListResponse)
async def get_characters(sort: str = "popular", limit: int = 12):
    chars = await to_thread.run_sync(cosmos.list_characters, sort, limit)
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
        raise RuntimeError("Cosmos DB connectivity failed during startup")
    # Seed characters (idempotent)
    await to_thread.run_sync(cosmos.seed_characters)
    print("Startup complete: Cosmos reachable and characters seeded (or already present)")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)