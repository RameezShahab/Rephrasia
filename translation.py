"""
translation.py — Bidirectional English ↔ Urdu translation.

Model: facebook/nllb-200-distilled-600M
  - Meta's No Language Left Behind, distilled 600 M variant (~2.5 GB).
  - Chosen for Hugging Face Spaces compatibility (memory < 8 GB).
  - Supports 200 languages via language token forcing.
"""

import logging
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from config import (
    TRANSLATION_MODEL,
    TRANSLATION_MAX_LENGTH,
    TRANSLATION_NUM_BEAMS,
)

logger = logging.getLogger(__name__)

_tokenizer = None
_model = None


def _load_model_resources():
    """Lazy-load the NLLB tokenizer and model (only once per process)."""
    global _tokenizer, _model
    if _tokenizer is None or _model is None:
        logger.info("Loading translation model: %s …", TRANSLATION_MODEL)
        _tokenizer = AutoTokenizer.from_pretrained(TRANSLATION_MODEL)
        _model = AutoModelForSeq2SeqLM.from_pretrained(TRANSLATION_MODEL)
        logger.info("Translation model loaded successfully.")
    return _tokenizer, _model


def _translate(text: str, src_lang: str, tgt_lang: str) -> str:
    """
    Internal helper — translates *text* from *src_lang* to *tgt_lang*.

    Args:
        text:     Source text.
        src_lang: NLLB language code for the source (e.g. 'eng_Latn').
        tgt_lang: NLLB language code for the target (e.g. 'urd_Arab').

    Returns:
        Translated string.
    """
    tokenizer, model = _load_model_resources()

    tokenizer.src_lang = src_lang
    inputs = tokenizer(
        text,
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
        )

    return tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)[0]


def translate_to_urdu(text: str) -> str:
    """Translate English text to Urdu."""
    try:
        result = _translate(text, src_lang="eng_Latn", tgt_lang="urd_Arab")
        logger.debug("Translated EN→UR (%d chars).", len(result))
        return result
    except Exception as exc:
        logger.exception("Translation EN→UR failed.")
        raise RuntimeError(f"Translation to Urdu failed: {exc}") from exc


def translate_to_english(text: str) -> str:
    """Translate Urdu text to English."""
    try:
        result = _translate(text, src_lang="urd_Arab", tgt_lang="eng_Latn")
        logger.debug("Translated UR→EN (%d chars).", len(result))
        return result
    except Exception as exc:
        logger.exception("Translation UR→EN failed.")
        raise RuntimeError(f"Translation to English failed: {exc}") from exc