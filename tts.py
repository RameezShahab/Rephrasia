"""Text-to-Speech functionality for translations."""

from gtts import gTTS
import os
import uuid
from pathlib import Path


# Create directory for audio files
AUDIO_DIR = Path("static/audio")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


def text_to_speech(text: str, language: str = "ur") -> str:
    """
    Convert text to speech and save as MP3 file.
    
    Args:
        text: The text to convert
        language: Language code (ur=Urdu, en=English)
    
    Returns:
        Relative path to the generated audio file
    """
    try:
        # Generate unique filename
        filename = f"{uuid.uuid4().hex}.mp3"
        filepath = AUDIO_DIR / filename
        
        # Create TTS object and save
        tts = gTTS(text=text, lang=language, slow=False)
        tts.save(str(filepath))
        
        # Return relative path for web access
        return f"audio/{filename}"
    
    except Exception as e:
        raise RuntimeError(f"TTS generation failed: {str(e)}")


def cleanup_old_audio_files(max_age_hours: int = 24):
    """Remove audio files older than max_age_hours."""
    import time
    current_time = time.time()
    
    for audio_file in AUDIO_DIR.glob("*.mp3"):
        file_age = (current_time - audio_file.stat().st_mtime) / 3600
        if file_age > max_age_hours:
            audio_file.unlink()
