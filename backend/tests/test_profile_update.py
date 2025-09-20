import asyncio
import importlib
from fastapi.testclient import TestClient
import os

os.environ.setdefault("ENTRA_API_AUDIENCE", "api://dummy")
os.environ.setdefault("ENTRA_TENANT_ID", "dummytenant")

# Patch entra_auth.validate_entra_token to bypass external JWKS call
import entra_auth  # type: ignore

async def fake_validate(_):
    return {"preferred_username": "tester@example.com", "email": "tester@example.com"}

entra_auth.validate_entra_token = fake_validate  # type: ignore

import cosmos  # ensure cosmos user functions available
import main as app_module

client = TestClient(app_module.app)

def test_patch_profile_flow(monkeypatch):
    # Force cosmos create/get functions to use in-memory dictionary
    store = {}
    def create_user(**kwargs):
        doc = {
            'id': kwargs['username'],
            'username': kwargs['username'],
            'email': kwargs['email'],
            'hashed_password': kwargs['hashed_password'],
            'gem_balance': 100,
            'is_active': True,
            'created_at': 0
        }
        store[doc['id']] = doc
        return doc
    def get_user_by_username(username):
        return store.get(username)
    def update_user(username, **fields):
        if username not in store:
            return None
        store[username].update(fields)
        return store[username]
    monkeypatch.setattr(cosmos, 'create_user', create_user)
    monkeypatch.setattr(cosmos, 'get_user_by_username', get_user_by_username)
    monkeypatch.setattr(cosmos, 'update_user', update_user)

    # Trigger auto-provision via /api/me
    r = client.get('/api/me', headers={'Authorization': 'Bearer faketoken'})
    assert r.status_code == 200
    user = r.json()
    assert user['username'] == 'tester@example.com'
    assert user['avatarUrl'] is None

    # Patch with avatar + terms
    r2 = client.patch('/api/me', json={'avatarUrl': 'http://avatar/test.png', 'agreeTerms': True}, headers={'Authorization': 'Bearer faketoken'})
    assert r2.status_code == 200
    updated = r2.json()
    assert updated['avatarUrl'] == 'http://avatar/test.png'
    assert updated['termsAgreedAt'] is not None