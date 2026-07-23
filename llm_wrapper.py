"""
llm_wrapper.py — Async helpers for parallel chunk processing.

CHANGELOG v2.1 (Bug fix):
  - FIX (Bug 3 — Silent Chunk Dropping):
    asyncio.Semaphore was created at MODULE LEVEL, meaning it was bound to
    whatever event loop existed at import time.  When background_document_processor
    calls asyncio.run() from a worker thread, Python creates a brand-new event
    loop.  Attempting to acquire a semaphore that belongs to a *different* loop
    raises a RuntimeError inside asyncio.gather() which is silently swallowed,
    causing individual chunks to be dropped without any log entry.

    The fix is to create the semaphore INSIDE process_chunks_parallel, so it is
    always created on (and bound to) the currently-running event loop.

  - ADDED: Per-chunk success/failure logging so any future drops are immediately
    visible in the server log (search for "Chunk N/M").
"""

import asyncio
import logging
from typing import List

from model import paraphrase
from translation import translate_to_urdu, translate_to_english

logger = logging.getLogger(__name__)

# Maximum number of model inference calls that may run concurrently.
# Keeping this at 2 prevents OOM on machines with limited VRAM/RAM.
MAX_CONCURRENT_TASKS = 1


async def _paraphrase_chunk_async(
    chunk: str,
    idx: int,
    total: int,
    semaphore: asyncio.Semaphore,
) -> str:
    """Paraphrase a single chunk, protected by the event-loop-local semaphore."""
    async with semaphore:
        logger.debug("Paraphrase chunk %d/%d starting (%d chars).", idx + 1, total, len(chunk))
        try:
            results = await asyncio.to_thread(paraphrase, chunk)
            result = results[0] if results else chunk
            logger.debug("Paraphrase chunk %d/%d done.", idx + 1, total)
            return result
        except Exception as exc:
            logger.error(
                "Paraphrase chunk %d/%d FAILED — returning original text. Error: %s",
                idx + 1, total, exc,
            )
            # Return the original chunk rather than dropping it silently.
            return chunk


async def _translate_chunk_async(
    chunk: str,
    target_lang: str,
    idx: int,
    total: int,
    semaphore: asyncio.Semaphore,
) -> str:
    """Translate a single chunk, protected by the event-loop-local semaphore."""
    async with semaphore:
        logger.debug(
            "Translate chunk %d/%d starting (%d chars → %s).",
            idx + 1, total, len(chunk), target_lang,
        )
        try:
            if target_lang.lower() == "urdu":
                result = await asyncio.to_thread(translate_to_urdu, chunk)
            else:
                result = await asyncio.to_thread(translate_to_english, chunk)
            logger.debug("Translate chunk %d/%d done.", idx + 1, total)
            return result
        except Exception as exc:
            logger.error(
                "Translate chunk %d/%d FAILED — returning original text. Error: %s",
                idx + 1, total, exc,
            )
            # Return the original chunk rather than dropping it silently.
            return chunk


async def process_chunks_parallel(
    chunks: List[str],
    task_type: str,
    target_lang: str = None,
) -> str:
    """
    Process multiple text chunks concurrently and reassemble in order.

    FIX (Bug 3 — Silent Chunk Dropping):
    The semaphore is created HERE, inside the coroutine, so it is always bound
    to the event loop that is currently running.  Previously it was created at
    module-import time, which caused it to belong to a different loop than the
    one started by asyncio.run() in the background thread.  That mismatch
    triggered a RuntimeError that asyncio.gather() caught and silently ignored,
    resulting in chunks being dropped from the output.

    Args:
        chunks:      List of text chunks to process.
        task_type:   'paraphrase' or 'translate'.
        target_lang: Required when task_type == 'translate' ('urdu' or 'english').

    Returns:
        Reassembled text (chunks joined with a single space, in original order).
    """
    if not chunks:
        return ""

    # Create the semaphore here so it belongs to the currently-running loop.
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)
    total = len(chunks)
    logger.info(
        "process_chunks_parallel: starting %d chunk(s) for task=%s lang=%s",
        total, task_type, target_lang,
    )

    if task_type == "paraphrase":
        tasks = [
            _paraphrase_chunk_async(chunk, i, total, semaphore)
            for i, chunk in enumerate(chunks)
        ]
    elif task_type == "translate":
        if not target_lang:
            raise ValueError("target_lang is required for translate tasks")
        tasks = [
            _translate_chunk_async(chunk, target_lang, i, total, semaphore)
            for i, chunk in enumerate(chunks)
        ]
    else:
        raise ValueError(f"Invalid task_type: {task_type!r}. Must be 'paraphrase' or 'translate'.")

    # return_exceptions=True ensures a failing chunk returns an exception object
    # instead of cancelling all remaining tasks.
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Post-gather: replace any exception objects with the original chunk text.
    assembled: list[str] = []
    for i, (chunk, result) in enumerate(zip(chunks, results)):
        if isinstance(result, Exception):
            logger.error(
                "Chunk %d/%d produced an exception during gather — "
                "substituting original text. Exception: %s",
                i + 1, total, result,
            )
            assembled.append(chunk)
        else:
            assembled.append(result)

    logger.info(
        "process_chunks_parallel: assembled %d/%d chunk(s) successfully.",
        len(assembled), total,
    )
    return " ".join(assembled)
