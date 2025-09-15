"""Entra ID token validation (authoritative; no local fallback).

This module enforces that all authenticated requests present a valid
Bearer access token issued by Microsoft Entra ID (v2 endpoint).

Behavior:
* Fetch & cache JWKS for 1 hour.
* Validate signature, issuer, audience, exp, nbf.
* Accept either the configured Application ID URI (api://APP_ID) or the
  bare client ID (some auth flows send that as aud) as audience.
* Returns claims dict on success, raises HTTP 401 on failure.
"""
from typing import Optional, Dict, Any, List
import os
import httpx
from cachetools import TTLCache
from jose import jwt
from fastapi import HTTPException, status

ENTRA_TENANT_ID = os.getenv("ENTRA_TENANT_ID")
ENTRA_API_AUDIENCE = os.getenv("ENTRA_API_AUDIENCE")  # Application ID URI or client ID

# B2C / External ID optional vars
ENTRA_B2C_POLICY = os.getenv("ENTRA_B2C_POLICY")  # e.g. B2C_1_SIGNUPSIGNIN
ENTRA_B2C_TENANT_PRIMARY_DOMAIN = os.getenv("ENTRA_B2C_TENANT_PRIMARY_DOMAIN")  # e.g. yourtenant.onmicrosoft.com
ENTRA_EXPECTED_ISSUER = os.getenv("ENTRA_EXPECTED_ISSUER")  # full override if provided

def _derive_b2c_issuer() -> Optional[str]:
    if ENTRA_EXPECTED_ISSUER:
        return ENTRA_EXPECTED_ISSUER.rstrip('/')
    if ENTRA_B2C_POLICY and ENTRA_B2C_TENANT_PRIMARY_DOMAIN:
        # B2C issuer pattern: https://<tenant>.b2clogin.com/<tenant>.onmicrosoft.com/<policy>/v2.0
        return f"https://{ENTRA_B2C_TENANT_PRIMARY_DOMAIN.split('.')[0]}.b2clogin.com/{ENTRA_B2C_TENANT_PRIMARY_DOMAIN}/{ENTRA_B2C_POLICY}/v2.0"
    return None

DERIVED_ISSUER = _derive_b2c_issuer() or (f"https://login.microsoftonline.com/{ENTRA_TENANT_ID}/v2.0" if ENTRA_TENANT_ID else None)

def _derive_jwks_url() -> Optional[str]:
    explicit = os.getenv("ENTRA_JWKS_URL")
    if explicit:
        return explicit
    if ENTRA_B2C_POLICY and ENTRA_B2C_TENANT_PRIMARY_DOMAIN:
        # B2C JWKS pattern adds /discovery/v2.0/keys after the policy segment
        tenant_prefix = ENTRA_B2C_TENANT_PRIMARY_DOMAIN.split('.')[0]
        return f"https://{tenant_prefix}.b2clogin.com/{ENTRA_B2C_TENANT_PRIMARY_DOMAIN}/{ENTRA_B2C_POLICY}/discovery/v2.0/keys"
    if ENTRA_TENANT_ID:
        return f"https://login.microsoftonline.com/{ENTRA_TENANT_ID}/discovery/v2.0/keys"
    return None

ENTRA_JWKS_URL = _derive_jwks_url()

if not ENTRA_API_AUDIENCE:
    raise RuntimeError("ENTRA_API_AUDIENCE is required for startup")
if not DERIVED_ISSUER:
    raise RuntimeError("Unable to derive issuer: set ENTRA_TENANT_ID or B2C variables (ENTRA_B2C_POLICY & ENTRA_B2C_TENANT_PRIMARY_DOMAIN) or ENTRA_EXPECTED_ISSUER.")

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

def _select_key(jwks: Dict[str, Any], kid: str):
    for jwk in jwks.get('keys', []):
        if jwk.get('kid') == kid:
            return jwk
    return None

async def validate_entra_token(auth_header: Optional[str]) -> Dict[str, Any]:
    if not auth_header or not auth_header.lower().startswith('bearer '):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = auth_header.split(' ', 1)[1]
    jwks = await _fetch_jwks()
    headers = jwt.get_unverified_header(token)
    kid = headers.get('kid')
    key = _select_key(jwks, kid)
    if key is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token key")
    accepted_audiences: List[str] = [ENTRA_API_AUDIENCE]
    # Add bare client ID variant if user supplied Application ID URI
    if ENTRA_API_AUDIENCE.startswith("api://"):
        maybe_client_id = ENTRA_API_AUDIENCE.replace("api://", "")
        accepted_audiences.append(maybe_client_id)
    try:
        claims = jwt.decode(
            token,
            key,
            algorithms=[key.get('alg', 'RS256'), 'RS256'],
            audience=accepted_audiences,
            issuer=DERIVED_ISSUER,
            options={
                'verify_aud': True,
                'verify_signature': True,
                'verify_exp': True,
                'verify_nbf': True,
            }
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Token validation failed: {exc}") from exc
    return claims

async def entra_dependency(authorization: Optional[str] = None):
    return await validate_entra_token(authorization)
