# -*- coding: utf-8 -*-
"""
OAuth2 + JWT authentication and Role-Based Access Control (RBAC) module for Causal AI and Small Language Models for Supply Chain Disruption Forecasting and Procurement Cost at Risk Estimation for Indian Automotive Component Sourcing FastAPI.
==================================================================================================

Provides:
  - Cryptographically secure HS256 JWT creation, signing, and verification.
  - Role-Based Access Control (RBAC) for roles: 'officer', 'analyst', and 'admin'.
  - Native fallback implementation using standard library hashlib/hmac when python-jose is not installed.
  - Production security validation: default JWT secret and admin password fail startup outside dev mode.
  - FastAPI dependency factories: require_roles(), require_officer, require_analyst, require_admin.

Environment variables:
  COUNTERVERSE_JWT_SECRET       - Signing secret (default: 'counterverse-dev-secret-CHANGE-IN-PROD')
  COUNTERVERSE_JWT_EXPIRE_M     - Token lifetime minutes (default: 60)
  COUNTERVERSE_ADMIN_PASSWORD   - Admin password plaintext (default: 'changeme')
  COUNTERVERSE_OFFICER_PASSWORD - Officer password plaintext (default: 'officerpass')
  COUNTERVERSE_ANALYST_PASSWORD - Analyst password plaintext (default: 'analystpass')
  COUNTERVERSE_AUTH_ENFORCE     - Set to 'true' to strictly enforce auth even in development mode
  ENVIRONMENT / COUNTERVERSE_ENV- Application environment ('development', 'test', 'production')
"""

import os
import json
import time
import hmac
import hashlib
import base64
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer

logger = logging.getLogger("counterverse.auth")

# ── Secrets and Configuration ─────────────────────────────────────
DEFAULT_JWT_SECRET = "counterverse-dev-secret-CHANGE-IN-PROD"
DEFAULT_ADMIN_PASSWORD = "changeme"

_JWT_SECRET = os.getenv("COUNTERVERSE_JWT_SECRET", DEFAULT_JWT_SECRET)
_JWT_ALGORITHM = "HS256"
_JWT_EXPIRE_MINUTES = int(os.getenv("COUNTERVERSE_JWT_EXPIRE_M", "60"))

# ── Users & Roles Database ─────────────────────────────────────────
# Supported roles: 'admin', 'officer', 'analyst'
_USERS_DB: Dict[str, Dict[str, Any]] = {
    "admin": {
        "username": "admin",
        "roles": ["admin", "officer", "analyst"],
        "env_var": "COUNTERVERSE_ADMIN_PASSWORD",
        "default_plain": DEFAULT_ADMIN_PASSWORD,
        "hashed_password": None,
        "disabled": False,
    },
    "officer": {
        "username": "officer",
        "roles": ["officer"],
        "env_var": "COUNTERVERSE_OFFICER_PASSWORD",
        "default_plain": "officerpass",
        "hashed_password": None,
        "disabled": False,
    },
    "analyst": {
        "username": "analyst",
        "roles": ["analyst"],
        "env_var": "COUNTERVERSE_ANALYST_PASSWORD",
        "default_plain": "analystpass",
        "hashed_password": None,
        "disabled": False,
    },
}

_hashes_initialized = False


# ── Password Hashing Helpers ───────────────────────────────────────
def _hash_pw(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with 100,000 iterations and fixed salt."""
    salt = b"counterverse-salt-v2"
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return key.hex()


def _verify_pw(password: str, hashed: str) -> bool:
    """Verify plaintext against stored PBKDF2 hash."""
    return hmac.compare_digest(_hash_pw(password), hashed)


def _ensure_users_initialized() -> None:
    """Lazily initialize user password hashes from environment or defaults."""
    global _hashes_initialized
    if not _hashes_initialized:
        for u in _USERS_DB.values():
            plain = os.getenv(u["env_var"], u["default_plain"])
            u["hashed_password"] = _hash_pw(plain)
        _hashes_initialized = True


# ── Base64URL Helpers for Standard Library JWT ────────────────────
def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    rem = len(s) % 4
    if rem > 0:
        s += "=" * (4 - rem)
    return base64.urlsafe_b64decode(s.encode("ascii"))


# ── JWT Creation & Verification ───────────────────────────────────
# Check for third-party jose or fallback to standard library HS256
_USE_JOSE = False
try:
    from jose import JWTError, jwt as _jose_jwt
    _USE_JOSE = True
except ImportError:
    _USE_JOSE = False

AUTH_AVAILABLE = True
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/token", auto_error=False)
http_bearer = HTTPBearer(auto_error=False)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a signed HS256 JWT access token containing subject, roles, and expiration.
    """
    secret = os.getenv("COUNTERVERSE_JWT_SECRET", DEFAULT_JWT_SECRET)
    payload = data.copy()
    exp_delta = expires_delta or timedelta(minutes=_JWT_EXPIRE_MINUTES)
    expire_epoch = int(time.time() + exp_delta.total_seconds())
    payload["exp"] = expire_epoch

    if _USE_JOSE:
        return _jose_jwt.encode(payload, secret, algorithm=_JWT_ALGORITHM)

    # Standard library HMAC-SHA256 implementation
    header_b64 = _b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(payload).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    sig = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    sig_b64 = _b64url_encode(sig)
    return f"{header_b64}.{payload_b64}.{sig_b64}"


def decode_token(token: str) -> dict:
    """
    Decode and verify a signed HS256 JWT access token.
    Raises ValueError on invalid signature or expired token.
    """
    secret = os.getenv("COUNTERVERSE_JWT_SECRET", DEFAULT_JWT_SECRET)

    if _USE_JOSE:
        try:
            return _jose_jwt.decode(token, secret, algorithms=[_JWT_ALGORITHM])
        except JWTError as exc:
            raise ValueError(f"Invalid token: {str(exc)}") from exc

    # Standard library HMAC-SHA256 decoding
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid token format: expected 3 dot-separated segments.")

    header_b64, payload_b64, sig_b64 = parts
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    expected_sig = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    expected_sig_b64 = _b64url_encode(expected_sig)

    if not hmac.compare_digest(sig_b64, expected_sig_b64):
        raise ValueError("Invalid token signature: HMAC verification failed.")

    try:
        payload_bytes = _b64url_decode(payload_b64)
        payload = json.loads(payload_bytes.decode("utf-8"))
    except Exception as e:
        raise ValueError(f"Malformed token payload: {str(e)}") from e

    exp = payload.get("exp")
    if exp is not None:
        if int(time.time()) > int(exp):
            raise ValueError("Token has expired.")

    return payload


def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Validate username and password against configured credentials.
    """
    _ensure_users_initialized()
    user = _USERS_DB.get(username)
    if not user:
        return None
    if not _verify_pw(password, user["hashed_password"]):
        return None
    return user


# ── Production Security Startup Check ──────────────────────────────
def verify_security_configuration() -> None:
    """
    Enforces security baseline on server startup.
    Default JWT secret and admin password MUST fail startup outside dev mode.
    """
    env = os.getenv("ENVIRONMENT", os.getenv("COUNTERVERSE_ENV", "development")).lower().strip()
    is_dev = env in ("development", "dev", "test", "testing", "local")

    current_secret = os.getenv("COUNTERVERSE_JWT_SECRET", DEFAULT_JWT_SECRET)
    current_admin_pw = os.getenv("COUNTERVERSE_ADMIN_PASSWORD", DEFAULT_ADMIN_PASSWORD)

    if not is_dev:
        if current_secret in (DEFAULT_JWT_SECRET, "", None):
            raise RuntimeError(
                f"FATAL SECURITY VIOLATION: COUNTERVERSE_JWT_SECRET must be configured with a secure key outside development mode (current env: '{env}')."
            )
        if current_admin_pw in (DEFAULT_ADMIN_PASSWORD, "admin", "password", "", None):
            raise RuntimeError(
                f"FATAL SECURITY VIOLATION: COUNTERVERSE_ADMIN_PASSWORD must be changed from the default ('changeme') outside development mode (current env: '{env}')."
            )

    logger.info(f"Security configuration verified (env: '{env}', is_dev: {is_dev}).")


# ── FastAPI Role-Based Dependencies ────────────────────────────────
def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(http_bearer),
) -> Dict[str, Any]:
    """
    FastAPI dependency extracting and validating the Bearer token.
    If auth enforcement is active or outside dev mode, requires a valid token.
    In development mode with no token provided, grants dev-user context for backward compatibility.
    """
    auth_enforce = os.getenv("COUNTERVERSE_AUTH_ENFORCE", "false").lower() in ("true", "1", "yes")
    env = os.getenv("ENVIRONMENT", os.getenv("COUNTERVERSE_ENV", "development")).lower().strip()
    is_dev = env in ("development", "dev", "test", "testing", "local")

    if credentials and credentials.credentials:
        token = credentials.credentials
        try:
            payload = decode_token(token)
            username = payload.get("sub")
            roles = payload.get("roles", [])
            if not username:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload: missing subject ('sub').",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return {
                "username": username,
                "roles": roles,
                "is_authenticated": True,
                "is_dev_fallback": False,
            }
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication failed: {str(exc)}",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # If no token provided:
    if not auth_enforce and is_dev:
        return {
            "username": "dev-user",
            "roles": ["admin", "officer", "analyst"],
            "is_authenticated": False,
            "is_dev_fallback": True,
        }

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Please provide a valid Bearer token.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_roles(*allowed_roles: str):
    """
    Dependency factory requiring the caller to possess at least one of `allowed_roles`
    or the 'admin' superuser role.
    """
    def _role_checker(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_roles = user.get("roles", [])
        if "admin" in user_roles:
            return user
        if any(r in user_roles for r in allowed_roles):
            return user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Forbidden: insufficient permissions. Endpoint requires role in {list(allowed_roles)}, current user roles: {user_roles}.",
        )
    return _role_checker


# Preconfigured role dependencies
require_officer = require_roles("officer")
require_analyst = require_roles("analyst")
require_admin = require_roles("admin")
require_authenticated = require_roles("officer", "analyst", "admin")
