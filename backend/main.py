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

load_dotenv()

app = FastAPI(title="Naughty Chats API", version="0.1.0")

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Mock database (in production this would be a real database)
users_db = {}
characters_db = [
    {
        "id": 1,
        "name": "Luna the Mystic",
        "avatarUrl": "https://via.placeholder.com/150",
        "shortDescription": "A mysterious sorceress from the ethereal realm",
        "tags": ["fantasy", "magical", "mysterious"],
        "ratingAvg": 4.8,
        "ratingCount": 127,
        "gemCostPerMessage": 5,
        "nsfwFlags": False,
        "lastActive": "2024-01-10T12:00:00Z"
    },
    {
        "id": 2,
        "name": "Zara the Adventurer",
        "avatarUrl": "https://via.placeholder.com/150",
        "shortDescription": "Bold explorer seeking thrilling adventures",
        "tags": ["adventure", "bold", "explorer"],
        "ratingAvg": 4.6,
        "ratingCount": 89,
        "gemCostPerMessage": 4,
        "nsfwFlags": False,
        "lastActive": "2024-01-10T11:30:00Z"
    },
    {
        "id": 3,
        "name": "Kai the Scholar",
        "avatarUrl": "https://via.placeholder.com/150",
        "shortDescription": "Wise academic with endless knowledge",
        "tags": ["intellectual", "wise", "academic"],
        "ratingAvg": 4.9,
        "ratingCount": 203,
        "gemCostPerMessage": 6,
        "nsfwFlags": False,
        "lastActive": "2024-01-10T10:45:00Z"
    }
]

# Pydantic models
class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str
    birthYear: int
    agreeTerms: bool

class UserLogin(BaseModel):
    identifier: str  # email or username
    password: str

class User(UserBase):
    id: int
    gemBalance: int
    isActive: bool

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User
    gemBalance: int

class CharacterSummary(BaseModel):
    id: int
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
    
    user = users_db.get(username)
    if user is None:
        raise credentials_exception
    return user

# API Endpoints
@app.get("/")
async def root():
    return {"message": "Naughty Chats API", "version": "0.1.0"}

@app.post("/api/auth/register", response_model=Token)
async def register(user: UserCreate):
    # Check if user already exists
    if user.email in users_db or user.username in users_db:
        raise HTTPException(
            status_code=400,
            detail="User with this email or username already exists"
        )
    
    # Validate age (must be 18+)
    current_year = datetime.now().year
    if current_year - user.birthYear < 18:
        raise HTTPException(
            status_code=400,
            detail="Must be 18 or older to register"
        )
    
    # Validate terms agreement
    if not user.agreeTerms:
        raise HTTPException(
            status_code=400,
            detail="Must agree to terms and conditions"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    user_id = len(users_db) + 1
    new_user = {
        "id": user_id,
        "email": user.email,
        "username": user.username,
        "hashed_password": hashed_password,
        "gemBalance": 100,  # Welcome bonus
        "isActive": True
    }
    
    # Store user (using username as key for simplicity)
    users_db[user.username] = new_user
    users_db[user.email] = new_user  # Allow login with email too
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    user_response = User(
        id=new_user["id"],
        email=new_user["email"],
        username=new_user["username"],
        gemBalance=new_user["gemBalance"],
        isActive=new_user["isActive"]
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_response,
        "gemBalance": new_user["gemBalance"]
    }

@app.post("/api/auth/login", response_model=Token)
async def login(user_credentials: UserLogin):
    # Find user by email or username
    user = users_db.get(user_credentials.identifier)
    
    if not user or not verify_password(user_credentials.password, user["hashed_password"]):
        raise HTTPException(
            status_code=400,
            detail="Invalid credentials"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    
    user_response = User(
        id=user["id"],
        email=user["email"],
        username=user["username"],
        gemBalance=user["gemBalance"],
        isActive=user["isActive"]
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_response,
        "gemBalance": user["gemBalance"]
    }

@app.get("/api/characters", response_model=CharacterListResponse)
async def get_characters(sort: str = "popular", limit: int = 12):
    """Get characters for the landing/explore page"""
    # Mock sorting logic
    if sort == "popular":
        sorted_chars = sorted(characters_db, key=lambda x: x["ratingAvg"], reverse=True)
    elif sort == "new":
        sorted_chars = sorted(characters_db, key=lambda x: x["lastActive"], reverse=True)
    else:  # fast_load
        sorted_chars = characters_db.copy()
    
    # Apply limit
    limited_chars = sorted_chars[:limit]
    
    return CharacterListResponse(
        items=[CharacterSummary(**char) for char in limited_chars],
        nextCursor=None  # For simplicity, no pagination in this demo
    )

@app.get("/api/me")
async def get_current_user_info(current_user = Depends(get_current_user)):
    """Get current user information"""
    return User(
        id=current_user["id"],
        email=current_user["email"],
        username=current_user["username"],
        gemBalance=current_user["gemBalance"],
        isActive=current_user["isActive"]
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)