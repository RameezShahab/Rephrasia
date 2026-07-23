"""
chunking.py — Semantic text splitting for Rephrasia's LLM pipeline.

Uses LangChain's RecursiveCharacterTextSplitter to break long documents into
overlapping chunks that respect natural language boundaries.

CHANGELOG v2.2:
  - FIX (Chunk Truncation / Missing Sections): Added get_paraphrase_chunks()
    with chunk_size=700 chars.  The previous default of 1500 chars caused T5
    to receive inputs of 300-360 tokens, which exceeded its 256-token limit and
    silently truncated ~25% of every chunk at the tokenizer.  At ~3.5 chars/token
    for typical English academic text, 700 chars maps to ~200 tokens — safely
    under the 256-token hard limit.

  - UNCHANGED: get_translation_chunks() with chunk_size=1200 (NLLB-tuned).
  - UNCHANGED: get_semantic_chunks() for general/caller-controlled use.
"""

import logging
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

# Separator priority: prefer paragraph breaks → sentence breaks → word breaks → char breaks.
_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

# Minimum required overlap to maintain cross-chunk sentence coherence.
MIN_CHUNK_OVERLAP = 100


def get_semantic_chunks(
    text: str,
    chunk_size: int = 1500,
    chunk_overlap: int = MIN_CHUNK_OVERLAP,
) -> list[str]:
    """
    Split *text* into overlapping chunks for general processing.

    Args:
        text:          The full input text to split.
        chunk_size:    Maximum characters per chunk (default 1500).
        chunk_overlap: Characters of context shared between adjacent chunks.
                       Clamped to at least MIN_CHUNK_OVERLAP.

    Returns:
        List of text chunks.
    """
    safe_overlap = max(chunk_overlap, MIN_CHUNK_OVERLAP)
    if safe_overlap != chunk_overlap:
        logger.warning(
            "chunk_overlap=%d is below minimum %d; clamping to %d.",
            chunk_overlap, MIN_CHUNK_OVERLAP, safe_overlap,
        )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=safe_overlap,
        separators=_SEPARATORS,
    )
    return splitter.split_text(text)


def get_paraphrase_chunks(text: str) -> list[str]:
    """
    Split *text* into chunks optimised for the T5 paraphrase model.

    FIX (Chunk Truncation / Missing Sections):
    humarin/chatgpt_paraphraser_on_T5_base has a hard 256-token generation limit.
    At ~3.5 chars/token for English academic prose, 1500-char chunks encode to
    300-360 tokens — causing the tokenizer to silently truncate the last ~25% of
    every chunk.  This is why entire case-study paragraphs disappeared from the
    output: they sat at the end of their respective chunks and were cut off before
    the model ever saw them.

    700-char chunks encode to ~175-220 tokens, giving a comfortable safety margin
    below the 256-token limit while still preserving full sentences.

    Overlap of 100 chars preserves sentence continuity across chunk boundaries.
    """
    return get_semantic_chunks(text, chunk_size=700, chunk_overlap=100)


def get_translation_chunks(text: str) -> list[str]:
    """
    Split *text* into chunks optimised for the NLLB translation model.

    The NLLB model has an effective input window of ~400-500 tokens.  At ~4 chars/token
    for English, this corresponds to roughly 1200-1600 characters.  Using 1200 chars
    (≈300 tokens) gives a safe margin that prevents silent tokeniser truncation inside
    _translate_chunk() and leaves headroom for the NLLB output to expand (Urdu is
    typically longer than English word-for-word).

    Overlap of 100 chars preserves sentence continuity across chunk boundaries.
    """
    return get_semantic_chunks(text, chunk_size=1200, chunk_overlap=100)
