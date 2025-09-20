from fastapi import Depends, HTTPException, Header
from typing import Optional
from .auth import decode_token

try:
    from .repositories.user_repository import UserRepository
except Exception:
    UserRepository = None


def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization header")
    token = parts[1]
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    sub = payload.get("sub")

    # attempt to enrich with user data from Cosmos-backed repo
    if UserRepository is not None:
        try:
            repo = UserRepository()
            user = repo.get_by_username(sub)
            if user:
                return {"user_id": sub, "username": user.get("username"), "email": user.get("email")}
        except Exception:
            # ignore repo errors and fall back
            pass

    return {"user_id": sub}
