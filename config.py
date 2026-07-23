"""
config.py — Centralized configuration constants for Rephrasia.
Adjust these values to tune model behaviour, limits, and paths.

CHANGELOG:
  v2.0 — Increased PARAPHRASE_MAX_LENGTH 128→256, TRANSLATION_MAX_LENGTH 128→512
         to prevent silent mid-sentence truncation on long inputs.
         Added repetition_penalty, no_repeat_ngram_size, and early_stopping for
         the paraphrase engine to eliminate hallucinated tokens & redundant phrasing.
         Added TRANSLATION_LONG_TEXT_THRESHOLD for internal chunk-routing in translation.py.
"""

# ── Model Names ───────────────────────────────────────────────────
PARAPHRASE_MODEL   = "humarin/chatgpt_paraphraser_on_T5_base"
TRANSLATION_MODEL  = "facebook/nllb-200-distilled-600M"   # ~2.5 GB (Spaces-friendly)
CHAT_MODEL         = "microsoft/DialoGPT-small"

# ── Paraphrase generation settings ───────────────────────────────
# FIX (Issue 2): max_length raised from 128→256 tokens to prevent mid-sentence truncation.
# FIX (Issue 2): no_repeat_ngram_size=3 suppresses repetitive / hallucinated token patterns.
# FIX (Issue 2): repetition_penalty=1.3 penalises reuse of low-frequency tokens (e.g. invented words).
# FIX (Issue 2): early_stopping=True prevents generation from drifting past natural EOS.
PARAPHRASE_NUM_BEAMS          = 5
PARAPHRASE_NUM_SEQUENCES      = 3
PARAPHRASE_MAX_LENGTH         = 256      # tokens  (was 128)
PARAPHRASE_NO_REPEAT_NGRAM    = 3        # forbid exact 3-gram repetition
PARAPHRASE_REPETITION_PENALTY = 1.3     # >1.0 penalises token reuse
PARAPHRASE_EARLY_STOPPING     = True

# ── Translation generation settings ──────────────────────────────
# FIX (Issue 3): max_length raised from 128→512 tokens to stop output truncation.
# FIX (Issue 3): TRANSLATION_LONG_TEXT_THRESHOLD — texts above this token count
#                are chunked *before* being passed to the model (see translation.py).
# FIX (Bug 2):  repetition_penalty=1.5 + no_repeat_ngram_size=3 break the NLLB
#               token-repetition loop ("Entrepreneurship"×40 times).
#               encoder_no_repeat_ngram_size=3 also prevents the model from copying
#               3-gram sequences from the source directly into the output (which is
#               the primary driver of the mixed Urdu/English injection seen in the
#               Airbnb section).
#               length_penalty=1.0 favours complete, natural-length outputs.
TRANSLATION_MAX_LENGTH               = 512    # tokens  (was 128)
TRANSLATION_NUM_BEAMS                = 5
TRANSLATION_LONG_TEXT_THRESHOLD      = 400   # tokens — route long texts through chunking
TRANSLATION_NO_REPEAT_NGRAM          = 3     # block exact 3-gram repetition in output
TRANSLATION_ENCODER_NO_REPEAT_NGRAM  = 3     # block source 3-grams being copied to output
TRANSLATION_REPETITION_PENALTY       = 1.5  # was 1.2; bumped harder to break the loop
TRANSLATION_LENGTH_PENALTY           = 1.0  # encourages full-length outputs

# ── Chat settings ─────────────────────────────────────────────────
CHAT_MAX_HISTORY_LENGTH = 1024
CHAT_TOP_K              = 50
CHAT_TOP_P              = 0.95
CHAT_TEMPERATURE        = 0.8
CHAT_SESSION_TTL_HOURS  = 2     # Sessions older than this are evicted

# ── Input validation ──────────────────────────────────────────────
MAX_TEXT_LENGTH    = 100000       # Characters; enforced server-side
MAX_BATCH_SIZE     = 20         # Max items in a batch request
MAX_UPLOAD_MB      = 16

# ── Static file cleanup ───────────────────────────────────────────
STATIC_CLEANUP_HOURS = 24

# ── Server ────────────────────────────────────────────────────────
PORT = 7860
