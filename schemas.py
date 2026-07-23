"""
schemas.py — Pydantic v2 models for request/response validation.

All new endpoints use these schemas for strict data validation
before any payload reaches core logic.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# ── Auth ──────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str = "User"
    avatar_initials: str = ""
    created_at: str = ""

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    user: UserResponse
    token: str


# ── Profile ───────────────────────────────────────────────────────────────────

class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8, max_length=128)


class ProfileUpdateResponse(BaseModel):
    id: str
    name: str
    email: str
    updated_at: str


# ── Preferences ───────────────────────────────────────────────────────────────

class PreferencesRequest(BaseModel):
    notifications: Optional[bool] = None
    dark_mode: Optional[bool] = None


class PreferencesResponse(BaseModel):
    notifications: bool
    dark_mode: bool
    updated_at: str


# ── Grammar ───────────────────────────────────────────────────────────────────

class GrammarCheckRequest(BaseModel):
    text: str = Field(..., min_length=1)

    @field_validator("text")
    @classmethod
    def strip_text(cls, v: str) -> str:
        return v.strip()


class GrammarIssue(BaseModel):
    type: str  # 'grammar' | 'punctuation' | 'style' | 'clarity'
    original: str
    suggestion: str
    position: dict  # {"start": int, "end": int}


class GrammarScores(BaseModel):
    grammar: int = Field(..., ge=0, le=100)
    readability: int = Field(..., ge=0, le=100)
    clarity: int = Field(..., ge=0, le=100)


class GrammarCheckResponse(BaseModel):
    corrected_text: str
    scores: GrammarScores
    issues: List[GrammarIssue] = []
    issue_count: int = 0


# ── History ───────────────────────────────────────────────────────────────────

class HistoryItem(BaseModel):
    id: str
    title: str
    type: str  # 'Paraphraser' | 'Translator' | 'Grammar Checker' | 'AI Chat'
    time: str  # Relative time string
    created_at: str  # ISO 8601


class HistoryListResponse(BaseModel):
    items: List[HistoryItem]
    total: int
    page: int
    limit: int


# ── Stats ─────────────────────────────────────────────────────────────────────

class ActivityItem(BaseModel):
    title: str
    time: str


class StatsResponse(BaseModel):
    words_generated: int
    documents_created: int
    ai_requests: int
    weekly_usage: List[int]
    recent_activity: List[ActivityItem]
