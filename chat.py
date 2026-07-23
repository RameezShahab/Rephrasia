"""
chat.py — Groq API-powered conversational assistant with session management.

Model: llama-3.1-8b-instant
Session history is maintained in-process RAM with TTL eviction.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

import groq

from config import CHAT_SESSION_TTL_HOURS

logger = logging.getLogger(__name__)

# Initialize Groq client with the provided API key
client = groq.Groq(api_key="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")
MODEL_NAME = "llama-3.1-8b-instant"


class ChatSessionManager:
    """
    Manages chat sessions, per-session token history, and conversation transcripts.
    """

    def __init__(self) -> None:
        self._sessions: Dict[str, Dict] = {}
        self._context: dict = {}  # Stores last_results from app.py
        
        self.system_prompt = (
            "You are Rephrasia Copilot, an advanced AI assistant integrated into "
            "the Rephrasia text processing platform. Be extremely helpful, "
            "concise, and accurate. Format your responses with Markdown where appropriate. "
            "CRITICAL: ALWAYS respond in English unless the user explicitly asks you "
            "to reply in another language. Even if the user provides text in Urdu, your analysis and response must be in English."
        )

    def _ensure_session(self, session_id: str | None) -> str:
        if not session_id or session_id not in self._sessions:
            session_id = uuid.uuid4().hex
            self._sessions[session_id] = {
                "transcript": [],
                "last_active": datetime.utcnow(),
            }
            logger.debug("New chat session created: %s", session_id)
        else:
            self._sessions[session_id]["last_active"] = datetime.utcnow()
        return session_id

    def _evict_expired_sessions(self) -> None:
        cutoff = datetime.utcnow() - timedelta(hours=CHAT_SESSION_TTL_HOURS)
        expired = [
            sid for sid, data in self._sessions.items()
            if data.get("last_active", datetime.utcnow()) < cutoff
        ]
        for sid in expired:
            del self._sessions[sid]
            logger.debug("Evicted expired chat session: %s", sid)

    def _generate_reply(self, transcript: List[Dict[str, str]], message: str) -> str:
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Add past context (limit to last 10 messages to save context window)
        for msg in transcript[-10:]:
            messages.append({"role": msg["role"], "content": msg["message"]})
            
        messages.append({"role": "user", "content": message})

        try:
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=0.7,
                max_tokens=1024,
            )
            return completion.choices[0].message.content
        except Exception as e:
            logger.error("Groq API error: %s", e)
            raise e

    def handle_message(
        self, session_id: str | None, message: str
    ) -> Tuple[str, str, List[Dict[str, str]]]:
        self._evict_expired_sessions()
        session_id = self._ensure_session(session_id)
        state = self._sessions[session_id]
        transcript: List[Dict[str, str]] = state["transcript"]

        try:
            reply = self._generate_reply(transcript, message)
        except Exception as exc:
            logger.exception("Chat model inference failed.")
            reply = "Sorry, I ran into an issue connecting to the AI."

        transcript.extend([
            {"role": "user",      "message": message},
            {"role": "assistant", "message": reply},
        ])
        return reply, session_id, list(transcript)

    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        return list(self._sessions.get(session_id, {}).get("transcript", []))

    def update_context(self, ctx: dict) -> None:
        self._context = ctx


chat_manager = ChatSessionManager()