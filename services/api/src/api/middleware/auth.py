"""JWT authentication middleware."""

from __future__ import annotations

import os
from typing import Any

import jwt
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-secret-key")
_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")

bearer_scheme = HTTPBearer(auto_error=False)


def verify_token(credentials: HTTPAuthorizationCredentials | None) -> dict[str, Any]:
    """Verify JWT token and return payload."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
        )

    try:
        payload = jwt.decode(
            credentials.credentials,
            _SECRET_KEY,
            algorithms=[_ALGORITHM],
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
        )
