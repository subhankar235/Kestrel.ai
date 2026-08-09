"""Clerk authentication and JWT verification module."""

from __future__ import annotations

import time
from typing import Any

import httpx
from fastapi import HTTPException, status
from jose import JWTError, jwt

from app.core.config import get_settings

_jwks_cache: dict[str, Any] = {}
_jwks_cache_expiry: float = 0.0
JWKS_CACHE_TTL_SECONDS = 3600  # Cache JWKS keys for 1 hour


async def fetch_clerk_jwks(jwks_url: str) -> dict[str, Any]:
    """Fetch JWKS keys from Clerk with in-memory caching."""
    global _jwks_cache, _jwks_cache_expiry

    now = time.time()
    if _jwks_cache and now < _jwks_cache_expiry:
        return _jwks_cache

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(jwks_url)
            response.raise_for_status()
            _jwks_cache = response.json()
            _jwks_cache_expiry = now + JWKS_CACHE_TTL_SECONDS
            return _jwks_cache
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Failed to fetch Clerk JWKS keys: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


async def verify_clerk_token(token: str) -> dict[str, Any]:
    """Verify Clerk-issued JWT token from Bearer authentication header."""
    settings = get_settings()

    if not token or not token.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing or empty",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        unverified_header = jwt.get_unverified_header(token)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed authentication token header",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    kid = unverified_header.get("kid")

    # If JWKS URL is configured in environment, verify RS256 signature against Clerk JWKS
    if settings.CLERK_JWKS_URL:
        jwks = await fetch_clerk_jwks(settings.CLERK_JWKS_URL)
        keys = jwks.get("keys", [])
        rsa_key = next((k for k in keys if k.get("kid") == kid), None)

        if not rsa_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Matching JWKS key ID not found in Clerk JWKS set",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=["RS256"],
                options={"verify_aud": False},
            )
            return payload
        except JWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid or expired Clerk token signature: {exc}",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc

    if settings.ENVIRONMENT == "production":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clerk JWKS URL must be configured in production",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Local/test fallback: decode claims without signature verification only when
    # explicitly running outside production. Integration tests replace this path.
    try:
        payload = jwt.get_unverified_claims(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Empty token claims",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return dict(payload)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
