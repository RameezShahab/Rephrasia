"""
translation.py — Bidirectional English ↔ Urdu translation.

Model: facebook/nllb-200-distilled-600M
  - Meta's No Language Left Behind, distilled 600 M variant (~2.5 GB).
  - Chosen for Hugging Face Spaces compatibility (memory < 8 GB).
  - Supports 200 languages via language token forcing.

CHANGELOG v2.0 (Bug fixes):
  - FIX (Issue 3 — Truncation): max_length raised from 128→512 tokens in both the
    tokenizer call AND model.generate(), so long sentences are no longer silently
    dropped mid-word.
  - FIX (Issue 3 — Long PDF text): translate_to_urdu() and translate_to_english()
    now detect long inputs (> TRANSLATION_LONG_TEXT_THRESHOLD tokens) and
    automatically split them into overlapping chunks via get_semantic_chunks().
    Each chunk is translated independently and the results are reassembled.
    This means a 5-page PDF no longer loses its second half.
  - FIX (Issue 1 — Stale Cache): Lazy-load guard uses explicit None check; model
    globals are re-evaluatable after force_reload_translation_model().
"""

import logging
import re
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

from config import (
    TRANSLATION_MODEL,
    TRANSLATION_MAX_LENGTH,
    TRANSLATION_NUM_BEAMS,
    TRANSLATION_LONG_TEXT_THRESHOLD,
    TRANSLATION_NO_REPEAT_NGRAM,
    TRANSLATION_ENCODER_NO_REPEAT_NGRAM,
    TRANSLATION_REPETITION_PENALTY,
    TRANSLATION_LENGTH_PENALTY,
)

logger = logging.getLogger(__name__)

_tokenizer: AutoTokenizer | None = None
_model: AutoModelForSeq2SeqLM | None = None


# ── Model loading ─────────────────────────────────────────────────────────────

def _load_model_resources() -> tuple[AutoTokenizer, AutoModelForSeq2SeqLM]:
    """Lazy-load the NLLB tokenizer and model (only once per process)."""
    global _tokenizer, _model
    if _tokenizer is None or _model is None:
        logger.info("Loading translation model: %s …", TRANSLATION_MODEL)
        _tokenizer = AutoTokenizer.from_pretrained(TRANSLATION_MODEL)
        _model = AutoModelForSeq2SeqLM.from_pretrained(TRANSLATION_MODEL)
        logger.info("Translation model loaded successfully.")
    return _tokenizer, _model


def force_reload_translation_model() -> None:
    """
    Force-evict the in-process translation model cache.

    Call this if config values change at runtime.  A full server restart
    is still required to pick up changes to config.py from __pycache__.
    """
    global _tokenizer, _model
    _tokenizer = None
    _model = None
    logger.warning("Translation model cache cleared — will reload on next request.")


# ── Proper Noun Protection ─────────────────────────────────────────────────────────────────────────
#
# WHY THIS IS NEEDED:
#   NLLB is a direct seq2seq translation model.  Unlike GPT-based LLMs it has
#   NO system-prompt mechanism for accepting natural-language rules like
#   "do not transliterate complex English names".
#
#   When NLLB encounters an unusual European surname like "Blecharczyk", it has
#   no equivalent token in Urdu script and falls back to phonetic reconstruction,
#   producing garbled output like "بلیبیا نیشن" ("Blebia Nation").
#
# THE FIX:
#   Before translation, replace multi-word English Title-Case sequences (which are
#   almost always people or company names) with indexed placeholders: @@PN0@@.
#   NLLB's SentencePiece tokenizer does not recognize @@ as a word-start boundary,
#   so the placeholder is typically passed through to the output unchanged.
#   After translation, a flexible regex (allowing for spaces NLLB might insert)
#   restores the original English name.
#
# SCOPE:
#   Only applied when translating FROM English (src_lang='eng_Latn').
#   Urdu-to-English does not need this since Urdu proper nouns are typically
#   short and NLLB handles them correctly in the Latin-script direction.
# ─────────────────────────────────────────────────────────────────────────────

# Matches 2 or more consecutive Title-Cased English words (minimum 3 chars each).
# This reliably identifies people names ("Nathan Blecharczyk", "Eric Yuan") and
# compound company names ("General Electric") without catching single words like
# "Tesla" or "Airbnb" which NLLB handles acceptably.
_PROPER_NOUN_RE = re.compile(
    r'\b([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})+)\b'
)

# Restoration pattern — allows for spaces NLLB may insert around the @@ markers.
_PN_RESTORE_RE = re.compile(r'@@\s*PN(\d+)\s*@@')


def _protect_proper_nouns(text: str) -> tuple[str, list[str]]:
    """
    Replace multi-word English Title-Case sequences with @@PNk@@ placeholders.

    Returns:
        (protected_text, list_of_original_nouns)
        The list index k corresponds to placeholder @@PNk@@.
    """
    originals: list[str] = []

    def replacer(m: re.Match) -> str:
        noun = m.group(0)
        idx = len(originals)
        originals.append(noun)
        return f"@@PN{idx}@@"

    return _PROPER_NOUN_RE.sub(replacer, text), originals


def _restore_proper_nouns(text: str, originals: list[str]) -> str:
    """
    Replace @@PNk@@ placeholders back with the original English proper nouns.

    Uses a flexible regex that tolerates spaces NLLB may insert around @@.
    If NLLB garbled the placeholder beyond recognition, the word is silently
    omitted (no worse than the previous garbled Urdu transliteration).
    """
    def restorer(m: re.Match) -> str:
        idx = int(m.group(1))
        if 0 <= idx < len(originals):
            return originals[idx]
        logger.warning("Proper noun placeholder @@PN%d@@ not found in originals.", idx)
        return m.group(0)

    return _PN_RESTORE_RE.sub(restorer, text)


# ── Core translation helper ───────────────────────────────────────────────────

def _translate_chunk(text: str, src_lang: str, tgt_lang: str) -> str:
    """
    Translate a *single* chunk of text from src_lang to tgt_lang.

    When translating FROM English (src_lang='eng_Latn'), multi-word proper nouns
    are protected with @@PNk@@ placeholders before inference and restored after,
    preventing NLLB from producing garbled phonetic transliterations of unusual
    surnames (e.g. "Blecharczyk" → "بلیبیا نیشن").

    Args:
        text:     Source text (should be ≤ TRANSLATION_LONG_TEXT_THRESHOLD tokens).
        src_lang: NLLB language code for the source (e.g. 'eng_Latn').
        tgt_lang: NLLB language code for the target (e.g. 'urd_Arab').

    Returns:
        Translated string with proper nouns preserved in their original form.
    """
    tokenizer, model = _load_model_resources()

    # Protect proper nouns when translating FROM English.
    originals: list[str] = []
    protected_text = text
    if src_lang == "eng_Latn":
        protected_text, originals = _protect_proper_nouns(text)
        if originals:
            logger.debug(
                "Protected %d proper noun(s): %s",
                len(originals),
                [n[:30] for n in originals],
            )

    tokenizer.src_lang = src_lang

    inputs = tokenizer(
        protected_text,
        return_tensors="pt",
        truncation=True,
        max_length=TRANSLATION_MAX_LENGTH,
    )

    target_lang_id = tokenizer.convert_tokens_to_ids(tgt_lang)

    with torch.no_grad():
        generated_tokens = model.generate(
            **inputs,
            forced_bos_token_id=target_lang_id,
            max_length=TRANSLATION_MAX_LENGTH,
            num_beams=TRANSLATION_NUM_BEAMS,
            # Decoder-side guard: block exact output 3-gram repetition
            no_repeat_ngram_size=TRANSLATION_NO_REPEAT_NGRAM,
            # Encoder-decoder guard: block source 3-grams from being copied verbatim
            # into the output.
            encoder_no_repeat_ngram_size=TRANSLATION_ENCODER_NO_REPEAT_NGRAM,
            # Token-reuse penalty bumped to 1.5 to break repetition loops.
            repetition_penalty=TRANSLATION_REPETITION_PENALTY,
            length_penalty=TRANSLATION_LENGTH_PENALTY,
        )

    raw_translation = tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)[0]

    # Restore proper nouns from placeholders.
    if originals:
        result = _restore_proper_nouns(raw_translation, originals)
        logger.debug("Restored proper nouns. Output snippet: %.60s", result)
    else:
        result = raw_translation

    return result


def _translate_long_text(text: str, src_lang: str, tgt_lang: str) -> str:
    """
    Translate arbitrarily long text by chunking, translating each chunk, and
    reassembling.

    FIX (Issue 3): This function is the core fix for PDF truncation.  Without it,
    a 5-page PDF passed directly to _translate_chunk() would be silently truncated
    at ~90 English words (128 tokens) and the rest of the document would vanish.

    With this function:
      1. The text is split into overlapping chunks via RecursiveCharacterTextSplitter
         (chunk_size=1200 chars, chunk_overlap=150 chars — inherited from chunking.py).
      2. Each chunk is translated independently.
      3. Results are joined with a space to form a continuous translation.

    The overlap ensures that sentences split across chunk boundaries are not
    mangled: the overlapping region gives the model enough left-context to
    translate the opening of the next chunk coherently.

    Args:
        text:     Full source text (any length).
        src_lang: NLLB source language code.
        tgt_lang: NLLB target language code.

    Returns:
        Full translated text as a single string.
    """
    # Import here to avoid circular imports at module level
    from chunking import get_semantic_chunks

    # Use a smaller chunk size for translation because the NLLB model has
    # a tighter effective context window than T5 paraphrase.
    chunks = get_semantic_chunks(text, chunk_size=1200, chunk_overlap=150)
    logger.info(
        "Long text detected — splitting into %d chunk(s) for translation "
        "(%d chars total).",
        len(chunks),
        len(text),
    )

    translated_parts: list[str] = []
    for idx, chunk in enumerate(chunks):
        logger.debug("Translating chunk %d/%d …", idx + 1, len(chunks))
        translated_parts.append(_translate_chunk(chunk, src_lang, tgt_lang))

    return " ".join(translated_parts)


def _is_long_text(text: str, src_lang: str) -> bool:
    """
    Return True if *text* exceeds TRANSLATION_LONG_TEXT_THRESHOLD tokens when
    encoded with the current tokenizer.

    This check is intentionally conservative: if the tokenizer isn't loaded yet
    we estimate length from character count (avg ~4 chars/token for Latin script,
    ~2.5 for Arabic/Urdu script).
    """
    try:
        tokenizer, _ = _load_model_resources()
        tokenizer.src_lang = src_lang
        token_count = len(tokenizer.encode(text, add_special_tokens=True))
        return token_count > TRANSLATION_LONG_TEXT_THRESHOLD
    except Exception:
        # Fall back to character-count heuristic if tokenizer not ready
        chars_per_token = 2.5 if src_lang.startswith("urd") else 4.0
        return (len(text) / chars_per_token) > TRANSLATION_LONG_TEXT_THRESHOLD


# ── Public API ────────────────────────────────────────────────────────────────

def translate_to_urdu(text: str) -> str:
    """
    Translate English text to Urdu.

    Automatically routes long texts through the chunked pipeline so that
    full PDF documents are translated without any content being dropped.
    """
    try:
        if _is_long_text(text, src_lang="eng_Latn"):
            result = _translate_long_text(text, src_lang="eng_Latn", tgt_lang="urd_Arab")
        else:
            result = _translate_chunk(text, src_lang="eng_Latn", tgt_lang="urd_Arab")
        logger.debug("Translated EN→UR (%d chars).", len(result))
        return result
    except Exception as exc:
        logger.exception("Translation EN→UR failed.")
        raise RuntimeError(f"Translation to Urdu failed: {exc}") from exc


def translate_to_english(text: str) -> str:
    """
    Translate Urdu text to English.

    Automatically routes long texts through the chunked pipeline so that
    full PDF documents are translated without any content being dropped.
    """
    try:
        if _is_long_text(text, src_lang="urd_Arab"):
            result = _translate_long_text(text, src_lang="urd_Arab", tgt_lang="eng_Latn")
        else:
            result = _translate_chunk(text, src_lang="urd_Arab", tgt_lang="eng_Latn")
        logger.debug("Translated UR→EN (%d chars).", len(result))
        return result
    except Exception as exc:
        logger.exception("Translation UR→EN failed.")
        raise RuntimeError(f"Translation to English failed: {exc}") from exc