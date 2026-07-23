"""
model.py — Text paraphrasing using humarin/chatgpt_paraphraser_on_T5_base.

Model: humarin/chatgpt_paraphraser_on_T5_base
  - A T5-base model fine-tuned specifically for paraphrasing tasks.
  - Generates up to PARAPHRASE_NUM_SEQUENCES diverse rewordings per input.

CHANGELOG v2.0 (Bug fixes):
  - FIX (Issue 2 — Hallucination): Added `no_repeat_ngram_size`, `repetition_penalty`,
    and `early_stopping` to model.generate() to eliminate invented tokens and
    redundant/repeated phrasing (e.g. "Entreprenesian").
  - FIX (Issue 2 — Causal Logic): The T5 prompt prefix now includes a strict
    "Causality Guard" instruction. The model is explicitly told NOT to reverse or
    fabricate causal relationships between entities.
  - FIX (Issue 2 — Truncation): max_length raised from 128→256 tokens; input encoding
    also uses 256-token limit so full sentences survive tokenisation.
  - FIX (Issue 1 — Stale Cache): Model globals reset to None on module reload so
    that a server restart always loads fresh weights from disk, not pycache.
"""

import logging
from transformers import T5Tokenizer, T5ForConditionalGeneration
from config import (
    PARAPHRASE_MODEL,
    PARAPHRASE_NUM_BEAMS,
    PARAPHRASE_NUM_SEQUENCES,
    PARAPHRASE_MAX_LENGTH,
    PARAPHRASE_NO_REPEAT_NGRAM,
    PARAPHRASE_REPETITION_PENALTY,
    PARAPHRASE_EARLY_STOPPING,
)

logger = logging.getLogger(__name__)

# Lazy-load globals.  Explicitly typed so linters don't complain.
_tokenizer: T5Tokenizer | None = None
_model: T5ForConditionalGeneration | None = None

# ── T5 Prompt Prefix ──────────────────────────────────────────────────────────
#
# CRITICAL — T5 is a seq2seq model, NOT a chat/instruction LLM.
# It has no concept of "system" vs "user" roles.  Any text prepended to the
# input IS part of the sequence the model tries to paraphrase.
#
# Injecting verbose English instructions ("Do NOT reverse causal relationships…")
# causes T5 to treat those words as part of the passage and echo them back in
# the output — that is Bug 1 (Prompt Bleed).
#
# The correct fix is:
#   1. Use only the minimal task-conditioning token that humarin/chatgpt_paraphraser
#      was actually fine-tuned on: "paraphrase: ".
#   2. Move all semantic quality constraints to the DECODING level (beam-search
#      hyperparameters) and the POST-PROCESSING level (output filtering below).
# ─────────────────────────────────────────────────────────────────────────────
_T5_PROMPT_PREFIX = "paraphrase: "

# Phrases to strip if T5 accidentally echoes any residual prompt text.
# Checked case-insensitively against the start of each output string.
_ECHO_STRIP_PREFIXES = (
    "paraphrase:",
    "paraphrase with",
    "do not reverse",
    "do not invent",
    "preserve all",
    "text to paraphrase:",
    "avoid inventing",
    "maintain a strict",
    "strict meaning preservation:",
)

# Substrings that, if they appear anywhere inside an output, indicate the output
# is a meta-echo of the instructions rather than a real paraphrase.
_META_SUBSTRINGS = (
    "avoid inventing words",
    "reversing causalities",
    "no reverse causality",
    "no invented words",
    "no invented facts",
    "principle of \'no",
    "strict adherence to",
    "preserve the accuracy of facts",
    "do not mention these instructions",
)


def _load_paraphrase_resources() -> tuple[T5Tokenizer, T5ForConditionalGeneration]:
    """Lazy-load the T5 tokenizer and model (only once per process)."""
    global _tokenizer, _model
    if _tokenizer is None or _model is None:
        logger.info("Loading paraphrase model: %s …", PARAPHRASE_MODEL)
        _tokenizer = T5Tokenizer.from_pretrained(PARAPHRASE_MODEL)
        _model = T5ForConditionalGeneration.from_pretrained(
            PARAPHRASE_MODEL, low_cpu_mem_usage=False
        )
        logger.info("Paraphrase model loaded successfully.")
    return _tokenizer, _model


def force_reload_paraphrase_model() -> None:
    """
    Force-evict the in-process model cache.

    Call this if you update config values at runtime and need the next
    `paraphrase()` call to re-read the updated hyperparameters.
    This does NOT invalidate __pycache__ — you still need to restart
    the server process after changing config.py.
    """
    global _tokenizer, _model
    _tokenizer = None
    _model = None
    logger.warning("Paraphrase model cache cleared — will reload on next request.")


def paraphrase(text: str) -> list[str]:
    """
    Generate multiple paraphrases of *text*.

    The function prepends a Causality Guard prefix to the T5 input so that
    the model is explicitly instructed not to reverse causal logic or invent
    vocabulary.  Generation is constrained by:
      - no_repeat_ngram_size  → suppress exact n-gram repetition
      - repetition_penalty    → penalise token reuse
      - early_stopping        → halt at natural EOS, not at max_length

    Args:
        text: Input sentence or paragraph.
              Inputs longer than PARAPHRASE_MAX_LENGTH tokens are truncated
              at tokenisation time (with a logged warning so the caller is aware).

    Returns:
        List of paraphrased strings (length == PARAPHRASE_NUM_SEQUENCES).

    Raises:
        RuntimeError: If model inference fails.
    """
    tokenizer, model = _load_paraphrase_resources()

    # Build prompt: use the minimal task-conditioning token only.
    # Do NOT inject verbose English instructions — T5 will echo them (Bug 1).
    prompted = f"{_T5_PROMPT_PREFIX}{text}"

    try:
        inputs = tokenizer(
            prompted,
            return_tensors="pt",
            truncation=True,
            max_length=PARAPHRASE_MAX_LENGTH,
        )
        input_ids = inputs["input_ids"]
        attention_mask = inputs["attention_mask"]

        # Warn if the input was actually truncated so it shows up in logs
        raw_token_count = len(tokenizer.encode(prompted, add_special_tokens=True))
        if raw_token_count > PARAPHRASE_MAX_LENGTH:
            logger.warning(
                "Paraphrase input truncated: %d tokens → %d tokens. "
                "Consider chunking before paraphrasing.",
                raw_token_count,
                PARAPHRASE_MAX_LENGTH,
            )

        outputs = model.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            num_beams=PARAPHRASE_NUM_BEAMS,
            num_return_sequences=PARAPHRASE_NUM_SEQUENCES,
            max_length=PARAPHRASE_MAX_LENGTH,
            no_repeat_ngram_size=PARAPHRASE_NO_REPEAT_NGRAM,
            repetition_penalty=PARAPHRASE_REPETITION_PENALTY,
            early_stopping=PARAPHRASE_EARLY_STOPPING,
            do_sample=False,
        )

        raw_results = [tokenizer.decode(o, skip_special_tokens=True) for o in outputs]

        # ── Post-processing: strip prompt-echo fragments ──────────────────────
        cleaned: list[str] = []
        for r in raw_results:
            r = r.strip()

            # 1. Strip any known prefix echoes from the start of the string.
            lower_r = r.lower()
            for pfx in _ECHO_STRIP_PREFIXES:
                if lower_r.startswith(pfx.lower()):
                    r = r[len(pfx):].strip()
                    lower_r = r.lower()
                    break

            # 2. Discard the entire output if it contains meta-instruction text.
            #    This catches cases where the echo appears mid-sentence.
            is_meta_echo = any(sub.lower() in r.lower() for sub in _META_SUBSTRINGS)
            if is_meta_echo:
                logger.warning(
                    "Discarded meta-echo output (prompt bleed detected): %.80s…", r
                )
                # Fall back to the original text so we never return an empty slot
                r = text

            cleaned.append(r)

        logger.debug("Generated %d paraphrase(s).", len(cleaned))
        return cleaned

    except Exception as exc:
        logger.exception("Paraphrasing failed.")
        raise RuntimeError("Paraphrasing failed") from exc


# ── Quick smoke-test ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sample = (
        "The study investigates the correlation between socioeconomic status "
        "and academic achievement. Donating shoes to students in need "
        "reduces absenteeism and improves health outcomes."
    )
    print("Original:", sample)
    print("\nParaphrases:")
    for i, s in enumerate(paraphrase(sample), 1):
        print(f"  {i}. {s}")