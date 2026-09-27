# -*- coding: utf-8 -*-
"""
OAuth2 + JWT authentication module for CounterVerse FastAPI.

Environment variables:
  COUNTERVERSE_JWT_SECRET      - signing secret (change in production!)
  COUNTERVERSE_JWT_EXPIRE_M    - token lifetime minutes (default 60)
  COUNTERVERSE_ADMIN_PASSWORD  - admin password plaintext (default: changeme)
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

_JWT_SECRET = os.getenv("COUNTERVERSE_JWT_SECRET", "counterverse-dev-secret-CHANGE-IN-PROD")
_JWT_ALGORITHM = "HS256"
_JWT_EXPIRE_MINUTES = int(os.getenv("COUNTERVERSE_JWT_EXPIRE_M", "60"))

AUTH_AVAILABLE = False
oauth2_scheme = None


def _noop_create_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    return "no-auth"


def _noop_decode_token(token: str) -> dict:
    return {}


def _noop_authenticate(username: str, password: str):
    return None


create_access_token = _noop_create_token
decode_token = _noop_decode_token
authenticate_user = _noop_authenticate

try:
    from jose import JWTError, jwt as _jwt
    from passlib.context import CryptContext
    from fastapi.security import OAuth2PasswordBearer

    _pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
    _admin_plain = os.getenv("COUNTERVERSE_ADMIN_PASSWORD", "changeme")

    # Lazy hashing — computed on first call to authenticate_user()
    _USERS_DB: dict = {
        "admin": {
            "username": "admin",
            "hashed_password": None,  # filled lazily
            "disabled": False,
        }
    }
    _hash_ready = False

    def _ensure_hash():
        global _hash_ready
        if not _hash_ready:
            _USERS_DB["admin"]["hashed_password"] = _pwd_ctx.hash(_admin_plain)
            _hash_ready = True

    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/token")
    AUTH_AVAILABLE = True

    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:  # type: ignore[misc]
        payload = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=_JWT_EXPIRE_MINUTES))
        payload["exp"] = expire
        return _jwt.encode(payload, _JWT_SECRET, algorithm=_JWT_ALGORITHM)

    def decode_token(token: str) -> dict:  # type: ignore[misc]
        try:
            return _jwt.decode(token, _JWT_SECRET, algorithms=[_JWT_ALGORITHM])
        except JWTError as exc:
            raise ValueError("Invalid token: " + str(exc)) from exc

    def authenticate_user(username: str, password: str):  # type: ignore[misc]
        _ensure_hash()
        user = _USERS_DB.get(username)
        if not user:
            return None
        if not _pwd_ctx.verify(password, user["hashed_password"]):
            return None
        return user

    logger.info("Auth module loaded (JWT + bcrypt).")

except ImportError:
    logger.debug("python-jose or passlib not installed; auth disabled (no-op mode).")
