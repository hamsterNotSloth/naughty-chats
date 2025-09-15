import os
import importlib
import types

import pytest
from jose import jwt
from fastapi.testclient import TestClient

# --- Test Setup -----------------------------------------------------------

# Set required Entra env vars BEFORE importing backend modules
os.environ.setdefault("ENTRA_TENANT_ID", "11111111-1111-1111-1111-111111111111")
os.environ.setdefault("ENTRA_API_AUDIENCE", "api://00000000-0000-0000-0000-000000000000")

# Static RSA key pair for test ONLY (NOT used in production) ----------------
TEST_PRIVATE_KEY = """-----BEGIN RSA PRIVATE KEY-----\nMIICXAIBAAKBgQDEkRh5YVdJWS3uFiJ+ah8u/7ZwE2v/nn3YKa0Rr5z5Z5HoI0AS\nxV4XgD2gkE1SYL4CuZ+0c7a6CbS8AGB/UB1zB+sLnaYlgqngPQHO3uQf2hFeRJ4y\n8Hh7xJBPwF3v4OkWSkfoCMetdNLW+KNw03FQalReuC8sn2gH5J9MeMSDgwIDAQAB\nAoGABV0UBj6VkJz0L5Gr1AT0H0Kk5U9l6K5WNXxGqQ4ZDwXdxV2qJ1I8RSn2M8vc\nJedTj2JbEz1QcL8Yo5TczjM63J/mwPS+0AVYJCMc1T/GMXIWk9jEM6RSl1Gkz9il\n+D0vAGxHyUzmx4aYUv2G5zkEYj4dXgW4OeeARkhPpgqro9UCQQD6Ss01gBG6bT0e\ndm8gWRPtVF+B3/fExpNjL0zSvlv0vr1g4Taeqcl2oTfxfOVIUvhUXL1nDJnP16C6\nqex6bS/3AkEAxH7IE4FXtmK2lIQ5uU6mI8ToL6vZqWbRXh3MyXVmFln+W6hpIv6C\nhd197gUTPK/PRk3v3MNlVNY4zudREKn7TwJBAJ+BeQS7EB/nkSYziPF4hI+tVSkA\n7YxnMiKdDLa6uYw9TMd5/TJHXrVMkgm1jFk5YFdnntbr+7LxySVVe6LSYVUCQAL3\nribvBd4CS0401lwVWEt6UjvlAU+hylgW1RHx+bQFNAnGjNr/H1ATvb9AJc7ZCfyA\nKwFAFZF5QSo5vPCaczECQEGxoH6JjMWvqE7d4AkpXJRiZD4bmX9Sy28sONv82J0i\nwVUyj/A4iX4vCJ0GOHG3WCYq22jxVXvuwyGZ7GmNBiM=\n-----END RSA PRIVATE KEY-----"""

TEST_PUBLIC_JWK = {
    "kty": "RSA",
    "use": "sig",
    "kid": "test",
    "alg": "RS256",
    # These values are derived from the private key above (shortened approach not critical for unit test semantics)
    # For simplicity we decode modulus/exponent via python-jose if needed; here we rely on jose accepting key directly.
}


def _issue_test_token():
    payload = {
        "aud": [os.environ["ENTRA_API_AUDIENCE"].replace("api://", ""), os.environ["ENTRA_API_AUDIENCE"]],
        "iss": f"https://login.microsoftonline.com/{os.environ['ENTRA_TENANT_ID']}/v2.0",
        "preferred_username": "tester@example.com",
        "email": "tester@example.com",
        "oid": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    }
    token = jwt.encode(payload, TEST_PRIVATE_KEY, algorithm="RS256", headers={"kid": "test"})
    return token


def _issue_b2c_test_token():
    """Issue a token shaped like a B2C user flow token (issuer + policy)."""
    os.environ.setdefault("ENTRA_B2C_POLICY", "B2C_1_SIGNUPSIGNIN")
    os.environ.setdefault("ENTRA_B2C_TENANT_PRIMARY_DOMAIN", "exampletenant.onmicrosoft.com")
    tenant_prefix = os.environ["ENTRA_B2C_TENANT_PRIMARY_DOMAIN"].split('.')[0]
    issuer = f"https://{tenant_prefix}.b2clogin.com/{os.environ['ENTRA_B2C_TENANT_PRIMARY_DOMAIN']}/{os.environ['ENTRA_B2C_POLICY']}/v2.0"
    payload = {
        "aud": [os.environ["ENTRA_API_AUDIENCE"].replace("api://", ""), os.environ["ENTRA_API_AUDIENCE"]],
        "iss": issuer,
        "preferred_username": "b2cuser@example.com",
        "email": "b2cuser@example.com",
        "oid": "bbbbbbbb-cccc-dddd-eeee-ffffffffffff",
    }
    return jwt.encode(payload, TEST_PRIVATE_KEY, algorithm="RS256", headers={"kid": "test"})


def _mock_fetch_jwks():  # noqa: D401
    return {"keys": [TEST_PUBLIC_JWK]}


def setup_module(module):  # noqa: D401
    # Import after env set; patch JWKS fetch before app usage
    import backend.entra_auth as entra_auth
    entra_auth._fetch_jwks = lambda: _mock_fetch_jwks()  # type: ignore
    # Patch async variant
    async def async_fetch():
        return _mock_fetch_jwks()
    entra_auth._fetch_jwks = async_fetch  # type: ignore

    # Mock cosmos functions before importing app
    import backend.cosmos as cosmos
    _store = {}

    def get_user_by_username(username: str):
        return _store.get(username)

    def create_user(username: str, email: str, hashed_password: str):
        doc = {
            'id': username,
            'username': username,
            'email': email,
            'hashed_password': hashed_password,
            'gem_balance': 100,
            'is_active': True,
            'created_at': 0,
        }
        _store[username] = doc
        return doc

    cosmos.get_user_by_username = get_user_by_username  # type: ignore
    cosmos.create_user = create_user  # type: ignore

    import backend.main as main  # noqa: F401  # triggers app creation


@pytest.fixture(scope="module")
def client():
    from backend.main import app
    return TestClient(app)


def test_me_unauthorized(client):
    resp = client.get("/api/me")
    assert resp.status_code == 401


def test_me_authorized_auto_provision(client):
    token = _issue_test_token()
    resp = client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["username"] == "tester@example.com"
    assert data["email"] == "tester@example.com"


def test_me_authorized_b2c_issuer(client):
    token = _issue_b2c_test_token()
    resp = client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["username"] == "b2cuser@example.com"
    assert data["email"] == "b2cuser@example.com"
