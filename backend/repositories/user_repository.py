from typing import Optional
from datetime import datetime

from ..db import get_users_container


class UserRepository:
    """Simple Cosmos-backed user repository. Returns minimal user dict with id, username, email, password_hash."""

    def __init__(self):
        self.container = get_users_container()

    def create_user(self, username: str, email: str, password_hash: str) -> dict:
        user = {
            "id": username,
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "created_at": datetime.utcnow().isoformat() + "Z",
        }
        if not self.container:
            # fallback to raising when container not available
            raise RuntimeError("Cosmos users container not configured")
        return self.container.create_item(user)

    def get_by_username(self, username: str) -> Optional[dict]:
        if not self.container:
            return None
        try:
            return self.container.read_item(item=username, partition_key=username)
        except Exception:
            return None

    def get_by_email(self, email: str) -> Optional[dict]:
        if not self.container:
            return None
        query = "SELECT * FROM c WHERE c.email=@email"
        params = [{"name": "@email", "value": email}]
        items = list(self.container.query_items(query=query, parameters=params, partition_key=None))
        return items[0] if items else None

    def upsert_refresh_token(self, user_id: str, refresh_token: str):
        if not self.container:
            raise RuntimeError("Cosmos users container not configured")
        # store refresh token with user doc for simplicity (rotate in prod)
        user = self.get_by_username(user_id)
        if not user:
            raise RuntimeError("user not found")
        user["refresh_token"] = refresh_token
        user["refresh_updated_at"] = datetime.utcnow().isoformat() + "Z"
        return self.container.upsert_item(user)
