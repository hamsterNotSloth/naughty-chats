from fastapi import APIRouter, HTTPException, Depends, Response
from pydantic import BaseModel
from typing import Optional
from ..auth import get_password_hash, verify_password, create_access_token, create_refresh_token, decode_token
from ..repositories.user_repository import UserRepository
import os

router = APIRouter(prefix="/api/v1/auth")

# instantiate repo (it handles None container fallback)
USER_REPO = UserRepository()
ENV = os.getenv("ENV", "dev")
COOKIE_SECURE = True if ENV == 'prod' else False


class RegisterReq(BaseModel):
    email: str
    username: str
    password: str
    birth_year: Optional[int] = None


class LoginReq(BaseModel):
    identifier: str
    password: str


class RefreshReq(BaseModel):
    refresh_token: Optional[str] = None


def _set_refresh_cookie(resp: Response, token: str):
    resp.set_cookie(
        key="refresh_token",
        value=token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        path="/",
        max_age=60 * 60 * 24 * 30,
    )


@router.post("/register")
def register(req: RegisterReq, resp: Response):
    existing = USER_REPO.get_by_username(req.username)
    if existing:
        raise HTTPException(status_code=400, detail="username exists")
    hashed = get_password_hash(req.password)
    try:
        created = USER_REPO.create_user(req.username, req.email, hashed)
    except RuntimeError:
        # fallback to ephemeral in-memory store for local dev
        raise HTTPException(status_code=500, detail="user store not configured")
    access = create_access_token(subject=created["id"])
    refresh = create_refresh_token(subject=created["id"])
    # persist refresh token
    USER_REPO.upsert_refresh_token(created["id"], refresh)
    _set_refresh_cookie(resp, refresh)
    return {"user": {"id": created["id"], "username": created["username"]}, "access": access}


@router.post("/login")
def login(req: LoginReq, resp: Response):
    # identifier can be username or email
    user = USER_REPO.get_by_username(req.identifier)
    if not user:
        user = USER_REPO.get_by_email(req.identifier)
    if not user or not verify_password(req.password, user.get("password_hash")):
        raise HTTPException(status_code=401, detail="invalid credentials")
    access = create_access_token(subject=user["id"])
    refresh = create_refresh_token(subject=user["id"])
    # persist refresh
    try:
        USER_REPO.upsert_refresh_token(user["id"], refresh)
    except RuntimeError:
        pass
    _set_refresh_cookie(resp, refresh)
    return {"access": access, "user": {"id": user["id"], "username": user["username"]}}


@router.post("/refresh")
def refresh(req: RefreshReq, resp: Response):
    token = req.refresh_token
    # if token not provided in body, try cookie
    if not token:
        # FastAPI doesn't expose cookies in this signature; read via Request would be needed.
        raise HTTPException(status_code=400, detail="refresh token required in body for this endpoint in dev")
    payload = decode_token(token)
    if not payload or payload.get("typ") != "refresh":
        raise HTTPException(status_code=401, detail="invalid refresh token")
    sub = payload.get("sub")
    # verify persisted token
    try:
        user = USER_REPO.get_by_username(sub)
        if user and user.get("refresh_token") != token:
            raise HTTPException(status_code=401, detail="refresh token revoked")
    except RuntimeError:
        # if store not configured we skip verification
        pass
    access = create_access_token(subject=sub)
    new_refresh = create_refresh_token(subject=sub)
    try:
        USER_REPO.upsert_refresh_token(sub, new_refresh)
    except RuntimeError:
        pass
    _set_refresh_cookie(resp, new_refresh)
    return {"access": access}


@router.post("/logout")
def logout(resp: Response):
    # clear cookie
    resp.delete_cookie("refresh_token", path="/")
    return {"ok": True}
