"""Entra ID token validation scaffold.

Phase 1 placeholder: provides a dependency that will later validate Access Tokens issued by Entra ID.
Currently returns None if Entra config not set, allowing legacy local JWT to operate.
"""
from typing import Optional, Dict, Any
import os
import httpx
from cachetools import TTLCache
from jose import jwt
from fastapi import HTTPException, status, Depends

ENTRA_TENANT_ID = os.getenv("ENTRA_TENANT_ID")
ENTRA_API_AUDIENCE = os.getenv("ENTRA_API_AUDIENCE")  # Application ID URI or client ID
ENTRA_JWKS_URL = os.getenv("ENTRA_JWKS_URL") or (
    f"https://login.microsoftonline.com/{ENTRA_TENANT_ID}/discovery/v2.0/keys" if ENTRA_TENANT_ID else None
)

_jwks_cache: TTLCache = TTLCache(maxsize=1, ttl=60 * 60)  # 1 hour

async def _fetch_jwks() -> Dict[str, Any]:
    if ENTRA_JWKS_URL is None:
        raise RuntimeError("JWKS URL not configured")
    if 'jwks' in _jwks_cache:
        return _jwks_cache['jwks']
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(ENTRA_JWKS_URL)
        resp.raise_for_status()
        data = resp.json()
        _jwks_cache['jwks'] = data
        return data

async def validate_entra_token(auth_header: Optional[str]) -> Optional[Dict[str, Any]]:
    """Validate Entra ID bearer token if configuration present.
    Returns claims dict if valid, None if Entra not configured.
    Raises HTTPException if configured but invalid.
    """
    if not (ENTRA_TENANT_ID and ENTRA_API_AUDIENCE):
        return None  # Not configured yet
    if not auth_header or not auth_header.lower().startswith('bearer '):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = auth_header.split(' ', 1)[1]
    jwks = await _fetch_jwks()
    # Simple key selection
    headers = jwt.get_unverified_header(token)
    kid = headers.get('kid')
    key = None
    for jwk in jwks.get('keys', []):
        if jwk.get('kid') == kid:
            key = jwk
            break
    if key is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token key")
    try:
        # Audience may be space separated scopes; we accept if contains ENTRA_API_AUDIENCE
        claims = jwt.decode(token, key, algorithms=[key.get('alg', 'RS256')], audience=ENTRA_API_AUDIENCE)
    except Exception as exc:  # broad until refined
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Token validation failed: {exc}") from exc
    issuer_expected = f"https://login.microsoftonline.com/{ENTRA_TENANT_ID}/v2.0"
    if claims.get('iss') != issuer_expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid issuer")
    return claims

async def entra_dependency(authorization: Optional[str] = None):
    return await validate_entra_token(authorization)
