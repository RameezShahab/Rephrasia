"""DialoGPT-powered chatbot with session history."""
from __future__ import annotations
import uuid
from typing import Dict, List, Tuple
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_NAME = "microsoft/DialoGPT-medium"
_tokenizer = None
_model = None

def _load_chatbot_resources():
    """Loads the tokenizer and model resources only once."""
    global _tokenizer, _model
    if _tokenizer is None or _model is None:
        # FIX: Added padding_side='left' for decoder-only models (like DialoGPT) 
        # to ensure correct token generation and suppress the warning.
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, padding_side='left')
        _model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
    return _tokenizer, _model

class ChatSessionManager:
    """Manages chat sessions, history tokens, and conversation transcripts."""
    def __init__(self) -> None:
        self._sessions: Dict[str, Dict[str, object]] = {}

    def _ensure_session(self, session_id: str | None) -> str:
        """Ensures a valid session ID exists, creating a new one if necessary."""
        if not session_id or session_id not in self._sessions:
            session_id = uuid.uuid4().hex
            self._sessions[session_id] = {
                "history_tokens": None,
                "transcript": []
            }
        return session_id

    def _generate_reply(self, history_tokens, message):
        """Encodes input, generates a response using the model, and decodes the result."""
        tokenizer, model = _load_chatbot_resources()
        
        # 1. Encode user message
        user_input_ids = tokenizer.encode(message + tokenizer.eos_token, return_tensors="pt")

        # 2. Concatenate history and current input
        if history_tokens is not None:
            bot_input_ids = torch.cat([history_tokens, user_input_ids], dim=-1)
        else:
            bot_input_ids = user_input_ids

        # 3. Generate response
        generated_ids = model.generate(
            bot_input_ids,
            max_length=1024,
            pad_token_id=tokenizer.eos_token_id,
            do_sample=True,
            top_k=50,
            top_p=0.95,
            temperature=0.8
        )
        
        # 4. Decode the reply (only the new part)
        reply_ids = generated_ids[:, bot_input_ids.shape[-1]:]
        reply_text = tokenizer.decode(reply_ids[0], skip_special_tokens=True)

        return generated_ids, reply_text or "I am still thinking about that."

    def handle_message(self, session_id: str | None, message: str) -> Tuple[str, str, List[Dict[str, str]]]:
        """Processes an incoming message, generates a reply, and updates session history."""
        session_id = self._ensure_session(session_id)
        state = self._sessions[session_id]
        transcript: List[Dict[str, str]] = state["transcript"]  # type: ignore[assignment]

        try:
            # Generate reply and update history tokens
            updated_tokens, reply = self._generate_reply(state["history_tokens"], message)
            state["history_tokens"] = updated_tokens
        except Exception as exc:
            reply = "Sorry, I ran into an issue generating a response."
            transcript.append({"role": "system", "message": str(exc)})
        
        # Update transcript
        transcript.append({"role": "user", "message": message})
        transcript.append({"role": "assistant", "message": reply})

        return reply, session_id, list(transcript)

    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        """Retrieves the full transcript for a given session ID."""
        state = self._sessions.get(session_id, {"transcript": []})
        return list(state["transcript"])  # type: ignore[index]

chat_manager = ChatSessionManager()