"""
model.py — Text paraphrasing using prithivida/parrot_paraphraser_on_T5.

Model: prithivida/parrot_paraphraser_on_T5
  - A T5-based paraphrasing model fine-tuned on diverse paraphrase corpora.
  - Generates up to PARAPHRASE_NUM_SEQUENCES diverse rewordings per input.
"""

import logging
from transformers import T5Tokenizer, T5ForConditionalGeneration
from config import (
    PARAPHRASE_MODEL,
    PARAPHRASE_NUM_BEAMS,
    PARAPHRASE_NUM_SEQUENCES,
    PARAPHRASE_MAX_LENGTH,
)

logger = logging.getLogger(__name__)

_tokenizer = None
_model = None


def _load_paraphrase_resources():
    """Lazy-load the T5 tokenizer and model (only once per process)."""
    global _tokenizer, _model
    if _tokenizer is None or _model is None:
        logger.info("Loading paraphrase model: %s …", PARAPHRASE_MODEL)
        _tokenizer = T5Tokenizer.from_pretrained(PARAPHRASE_MODEL)
        _model = T5ForConditionalGeneration.from_pretrained(PARAPHRASE_MODEL, low_cpu_mem_usage=False)
        logger.info("Paraphrase model loaded successfully.")
    return _tokenizer, _model


def paraphrase(text: str) -> list[str]:
    """
    Generate multiple paraphrases of *text*.

    Args:
        text: Input sentence or paragraph (max ~500 chars recommended).

    Returns:
        List of paraphrased strings (length == PARAPHRASE_NUM_SEQUENCES).

    Raises:
        RuntimeError: If model inference fails.
    """
    tokenizer, model = _load_paraphrase_resources()

    try:
        input_ids = tokenizer.encode(
            f"paraphrase: {text}",
            return_tensors="pt",
            truncation=True,
            max_length=PARAPHRASE_MAX_LENGTH,
        )

        outputs = model.generate(
            input_ids=input_ids,
            num_beams=PARAPHRASE_NUM_BEAMS,
            num_return_sequences=PARAPHRASE_NUM_SEQUENCES,
            max_length=PARAPHRASE_MAX_LENGTH,
        )

        results = [tokenizer.decode(o, skip_special_tokens=True) for o in outputs]
        logger.debug("Generated %d paraphrase(s).", len(results))
        return results

    except Exception as exc:
        logger.exception("Paraphrasing failed.")
        raise RuntimeError("Paraphrasing failed") from exc


# ── Quick smoke-test ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sample = "The study investigates the correlation between socioeconomic status and academic achievement."
    print("Original:", sample)
    print("\nParaphrases:")
    for i, s in enumerate(paraphrase(sample), 1):
        print(f"  {i}. {s}")