"""
chat.py — DialoGPT-powered conversational assistant with session management.

Model: microsoft/DialoGPT-medium
  - A GPT-2 variant fine-tuned on 147 M Reddit conversations.
  - Session history is maintained in-process RAM with TTL eviction.

Session TTL:
  - Sessions inactive for > CHAT_SESSION_TTL_HOURS are automatically evicted
    on the next handle_message() call to prevent unbounded memory growth.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from config import (
    CHAT_MODEL,
    CHAT_MAX_HISTORY_LENGTH,
    CHAT_TOP_K,
    CHAT_TOP_P,
    CHAT_TEMPERATURE,
    CHAT_SESSION_TTL_HOURS,
)

logger = logging.getLogger(__name__)

_tokenizer = None
_model = None


def _load_chatbot_resources():
    """Lazy-load the DialoGPT tokenizer and model (only once per process)."""
    global _tokenizer, _model
    if _tokenizer is None or _model is None:
        logger.info("Loading chat model: %s …", CHAT_MODEL)
        # padding_side='left' is required for decoder-only causal LMs
        _tokenizer = AutoTokenizer.from_pretrained(CHAT_MODEL, padding_side="left")
        _model = AutoModelForCausalLM.from_pretrained(CHAT_MODEL)
        logger.info("Chat model loaded successfully.")
    return _tokenizer, _model


class ChatSessionManager:
    """
    Manages chat sessions, per-session token history, and conversation transcripts.

    Features:
      - Lazy model loading on first message.
      - TTL-based session eviction (CHAT_SESSION_TTL_HOURS) to cap RAM usage.
      - Context-aware definition lookup for recent rephrase/translate results.
    """

    def __init__(self) -> None:
        self._sessions: Dict[str, Dict] = {}
        self._context: dict = {}  # Stores last_results from app.py

    # ── Internal helpers ────────────────────────────────────────────────────

    def _ensure_session(self, session_id: str | None) -> str:
        """Return a valid session ID, creating a new session if necessary."""
        if not session_id or session_id not in self._sessions:
            session_id = uuid.uuid4().hex
            self._sessions[session_id] = {
                "history_tokens": None,
                "transcript": [],
                "last_active": datetime.utcnow(),
            }
            logger.debug("New chat session created: %s", session_id)
        else:
            self._sessions[session_id]["last_active"] = datetime.utcnow()
        return session_id

    def _evict_expired_sessions(self) -> None:
        """Remove sessions that have been inactive longer than TTL."""
        cutoff = datetime.utcnow() - timedelta(hours=CHAT_SESSION_TTL_HOURS)
        expired = [
            sid for sid, data in self._sessions.items()
            if data.get("last_active", datetime.utcnow()) < cutoff
        ]
        for sid in expired:
            del self._sessions[sid]
            logger.debug("Evicted expired chat session: %s", sid)

    def _generate_reply(
        self, history_tokens: torch.Tensor | None, message: str
    ) -> Tuple[torch.Tensor, str]:
        """Encode input, run model inference, decode and return (tokens, reply)."""
        tokenizer, model = _load_chatbot_resources()

        user_input_ids = tokenizer.encode(
            message + tokenizer.eos_token, return_tensors="pt"
        )

        bot_input_ids = (
            torch.cat([history_tokens, user_input_ids], dim=-1)
            if history_tokens is not None
            else user_input_ids
        )

        with torch.no_grad():
            generated_ids = model.generate(
                bot_input_ids,
                max_length=CHAT_MAX_HISTORY_LENGTH,
                pad_token_id=tokenizer.eos_token_id,
                do_sample=True,
                top_k=CHAT_TOP_K,
                top_p=CHAT_TOP_P,
                temperature=CHAT_TEMPERATURE,
            )

        reply_ids = generated_ids[:, bot_input_ids.shape[-1]:]
        reply_text = tokenizer.decode(reply_ids[0], skip_special_tokens=True)
        return generated_ids, reply_text or "I am still thinking about that."

    # ── Public API ───────────────────────────────────────────────────────────

    def handle_message(
        self, session_id: str | None, message: str
    ) -> Tuple[str, str, List[Dict[str, str]]]:
        """
        Process *message*, generate a reply, update session state, and return
        (reply, session_id, transcript).

        Definition queries (messages starting with 'define') are answered
        directly from the stored rephrase/translate context without calling
        the model.
        """
        # Evict stale sessions opportunistically on each call
        self._evict_expired_sessions()

        session_id = self._ensure_session(session_id)
        state = self._sessions[session_id]
        transcript: List[Dict[str, str]] = state["transcript"]

        # ── Definition shortcut ──────────────────────────────────────────────
        lowered = message.lower().strip()
        if lowered.startswith("define"):
            term = lowered[len("define"):].strip().strip('"\'')
            definition = self._lookup_definition(term)
            reply = definition or f"I couldn't find a definition for '{term}' in the recent results."
            transcript.extend([
                {"role": "user",      "message": message},
                {"role": "assistant", "message": reply},
            ])
            return reply, session_id, list(transcript)

        # ── Model inference ──────────────────────────────────────────────────
        try:
            updated_tokens, reply = self._generate_reply(state["history_tokens"], message)
            state["history_tokens"] = updated_tokens
        except Exception as exc:
            logger.exception("Chat model inference failed.")
            reply = "Sorry, I ran into an issue generating a response."
            transcript.append({"role": "system", "message": str(exc)})

        transcript.extend([
            {"role": "user",      "message": message},
            {"role": "assistant", "message": reply},
        ])
        return reply, session_id, list(transcript)

    def _lookup_definition(self, term: str) -> str | None:
        """Check rephrase/translate context for *term* and return a definition string."""
        translate_text = self._context.get("translate", "")
        if translate_text and term in translate_text.lower():
            return f"Translation: {translate_text}"
        for para in self._context.get("rephrase", []):
            if term in para.lower():
                return f"Paraphrase: {para}"
        return None

    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        """Return the full conversation transcript for *session_id*."""
        return list(self._sessions.get(session_id, {}).get("transcript", []))

    def update_context(self, ctx: dict) -> None:
        """Store the latest rephrase/translate results for definition lookups."""
        self._context = ctx


chat_manager = ChatSessionManager()