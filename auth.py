"""
auth.py — JWT authentication utilities with in-memory user store.

This module provides registration, login, and token verification for the
Rephrasia AI backend.  Users are stored in-process RAM (mock database) —
swap _users_db for a real database adapter in production.

Dependencies: PyJWT, werkzeug (already installed via Flask)
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

from flask import request, jsonify

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────

JWT_SECRET = "rephrasia-dev-secret-change-in-production"  # TODO: move to .env
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24

# ── In-Memory User Store (Mock DB) ───────────────────────────────────────────

_users_db: dict[str, dict] = {}


def _make_initials(name: str) -> str:
    """Generate 2-letter initials from a full name."""
    parts = name.strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return name[:2].upper() if name else "??"


# ── Public API ────────────────────────────────────────────────────────────────

def register_user(name: str, email: str, password: str) -> tuple[dict, str]:
    """
    Register a new user.

    Returns:
        (user_dict, jwt_token)

    Raises:
        ValueError: If email is already registered.
    """
    email_lower = email.lower()
    for user in _users_db.values():
        if user["email"] == email_lower:
            raise ValueError("Email already registered")

    user_id = uuid.uuid4().hex
    now = datetime.now(timezone.utc).isoformat()

    user = {
        "id": user_id,
        "name": name,
        "email": email_lower,
        "password_hash": generate_password_hash(password),
        "role": "AI Researcher",
        "avatar_initials": _make_initials(name),
        "created_at": now,
        "preferences": {
            "notifications": True,
            "dark_mode": True,
        },
    }
    _users_db[user_id] = user
    token = _create_token(user_id)
    logger.info("User registered: %s (%s)", name, email_lower)
    return _safe_user(user), token


def login_user(email: str, password: str) -> tuple[dict, str]:
    """
    Authenticate a user.

    Returns:
        (user_dict, jwt_token)

    Raises:
        ValueError: If credentials are invalid.
    """
    email_lower = email.lower()
    for user in _users_db.values():
        if user["email"] == email_lower:
            if check_password_hash(user["password_hash"], password):
                token = _create_token(user["id"])
                logger.info("User logged in: %s", email_lower)
                return _safe_user(user), token
            break
    raise ValueError("Invalid email or password")


def get_user(user_id: str) -> Optional[dict]:
    """Return a safe (no password_hash) user dict, or None."""
    user = _users_db.get(user_id)
    return _safe_user(user) if user else None


def update_user(user_id: str, **kwargs) -> dict:
    """Update fields on an existing user. Returns updated user dict."""
    user = _users_db.get(user_id)
    if not user:
        raise ValueError("User not found")

    if "name" in kwargs and kwargs["name"]:
        user["name"] = kwargs["name"]
        user["avatar_initials"] = _make_initials(kwargs["name"])
    if "email" in kwargs and kwargs["email"]:
        user["email"] = kwargs["email"].lower()
    if "password" in kwargs and kwargs["password"]:
        user["password_hash"] = generate_password_hash(kwargs["password"])

    return _safe_user(user)


def update_preferences(user_id: str, notifications: bool | None, dark_mode: bool | None) -> dict:
    """Update user preferences. Returns updated preferences dict."""
    user = _users_db.get(user_id)
    if not user:
        raise ValueError("User not found")

    prefs = user.setdefault("preferences", {"notifications": True, "dark_mode": True})
    if notifications is not None:
        prefs["notifications"] = notifications
    if dark_mode is not None:
        prefs["dark_mode"] = dark_mode

    return prefs


# ── JWT Helpers ───────────────────────────────────────────────────────────────

def _create_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> Optional[str]:
    """Verify JWT and return user_id, or None if invalid/expired."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        logger.warning("JWT expired.")
        return None
    except jwt.InvalidTokenError:
        logger.warning("Invalid JWT.")
        return None


# ── Flask Decorator ───────────────────────────────────────────────────────────

def require_auth(f):
    """
    Flask route decorator that requires a valid JWT in the Authorization header.

    On success, injects `current_user_id` as a keyword argument.
    On failure, returns 401 JSON error.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Unauthorized — missing Bearer token"}), 401

        token = auth_header[7:]
        user_id = verify_token(token)
        if not user_id:
            return jsonify({"error": "Unauthorized — invalid or expired token"}), 401

        if user_id not in _users_db:
            return jsonify({"error": "Unauthorized — user not found"}), 401

        kwargs["current_user_id"] = user_id
        return f(*args, **kwargs)

    return decorated


def require_admin(f):
    """
    Flask route decorator that requires a valid JWT in the Authorization header
    and an 'Admin' role.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Unauthorized — missing Bearer token"}), 401

        token = auth_header[7:]
        user_id = verify_token(token)
        if not user_id:
            return jsonify({"error": "Unauthorized — invalid or expired token"}), 401

        user = _users_db.get(user_id)
        if not user:
            return jsonify({"error": "Unauthorized — user not found"}), 401

        if user.get("role") != "Admin":
            return jsonify({"error": "Forbidden — requires Admin privileges"}), 403

        # We can still inject the user_id if needed
        kwargs["current_user_id"] = user_id
        return f(*args, **kwargs)

    return decorated


# ── Internal Helpers ──────────────────────────────────────────────────────────

def _safe_user(user: dict) -> dict:
    """Return a copy of the user dict without sensitive fields."""
    return {k: v for k, v in user.items() if k != "password_hash"}
