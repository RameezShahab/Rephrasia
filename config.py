"""
config.py — Centralized configuration constants for Rephrasia.
Adjust these values to tune model behaviour, limits, and paths.
"""

# ── Model Names ───────────────────────────────────────────────────
PARAPHRASE_MODEL   = "humarin/chatgpt_paraphraser_on_T5_base"
TRANSLATION_MODEL  = "facebook/nllb-200-distilled-600M"   # ~2.5 GB (Spaces-friendly)
CHAT_MODEL         = "microsoft/DialoGPT-medium"

# ── Paraphrase settings ───────────────────────────────────────────
PARAPHRASE_NUM_BEAMS     = 5
PARAPHRASE_NUM_SEQUENCES = 3
PARAPHRASE_MAX_LENGTH    = 128

# ── Translation settings ──────────────────────────────────────────
TRANSLATION_MAX_LENGTH = 128
TRANSLATION_NUM_BEAMS  = 5

# ── Chat settings ─────────────────────────────────────────────────
CHAT_MAX_HISTORY_LENGTH = 1024
CHAT_TOP_K              = 50
CHAT_TOP_P              = 0.95
CHAT_TEMPERATURE        = 0.8
CHAT_SESSION_TTL_HOURS  = 2     # Sessions older than this are evicted

# ── Input validation ──────────────────────────────────────────────
MAX_TEXT_LENGTH    = 1000       # Characters; enforced server-side
MAX_BATCH_SIZE     = 20         # Max items in a batch request
MAX_UPLOAD_MB      = 16

# ── Static file cleanup ───────────────────────────────────────────
STATIC_CLEANUP_HOURS = 24

# ── Server ────────────────────────────────────────────────────────
PORT = 7860
