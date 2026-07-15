"""
tts.py — Text-to-Speech using Google Text-to-Speech (gTTS).

Generates MP3 files under static/audio/.
Call cleanup_old_audio_files() periodically to prevent unbounded disk growth.
"""

import io
import logging
import time
import uuid
from pathlib import Path

from gtts import gTTS

logger = logging.getLogger(__name__)

AUDIO_DIR = Path("static/audio")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Supported language codes (gTTS BCP-47 codes)
SUPPORTED_LANG_CODES = {"ur", "en"}


def text_to_speech(text: str, language: str = "ur") -> str:
    """
    Convert *text* to speech and save as MP3.

    Args:
        text:     Text to synthesize.
        language: BCP-47 language code — 'ur' (Urdu) or 'en' (English).

    Returns:
        Relative path for web access (e.g. 'audio/abc123.mp3').

    Raises:
        ValueError:  If *language* is not supported.
        RuntimeError: On gTTS synthesis failure.
    """
    if language not in SUPPORTED_LANG_CODES:
        raise ValueError(
            f"Unsupported TTS language '{language}'. "
            f"Choose from: {', '.join(sorted(SUPPORTED_LANG_CODES))}"
        )

    try:
        filename = f"{uuid.uuid4().hex}.mp3"
        filepath = AUDIO_DIR / filename

        tts = gTTS(text=text, lang=language, slow=False)
        tts.save(str(filepath))

        logger.debug("TTS generated: %s (lang=%s, %d chars)", filename, language, len(text))
        return f"audio/{filename}"

    except Exception as exc:
        logger.exception("TTS generation failed.")
        raise RuntimeError(f"TTS generation failed: {exc}") from exc


def cleanup_old_audio_files(max_age_hours: int = 24) -> int:
    """
    Delete MP3 files older than *max_age_hours*.

    Returns:
        Number of files deleted.
    """
    current_time = time.time()
    deleted = 0
    for audio_file in AUDIO_DIR.glob("*.mp3"):
        age_hours = (current_time - audio_file.stat().st_mtime) / 3600
        if age_hours > max_age_hours:
            audio_file.unlink()
            deleted += 1
    if deleted:
        logger.info("Cleaned up %d old audio file(s).", deleted)
    return deleted
