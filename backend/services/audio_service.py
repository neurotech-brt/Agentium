"""
Audio Service for Agentium — Phase 10.3.

Wraps OpenAI Whisper (STT) and OpenAI TTS APIs into a reusable service
layer. The existing ``voice.py`` route provides HTTP endpoints; this
service is the logic layer that can also be called by the ChannelManager
for voice messages on external platforms.
"""

import io
import logging
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_AUDIO_SIZE = 25 * 1024 * 1024  # 25 MB (OpenAI limit)

SUPPORTED_AUDIO_TYPES = [
    "audio/mpeg", "audio/mp3", "audio/mp4", "audio/wav",
    "audio/webm", "audio/ogg", "audio/m4a", "audio/flac",
]

AVAILABLE_TTS_VOICES = [
    {"id": "alloy", "name": "Alloy", "description": "Neutral and balanced"},
    {"id": "echo", "name": "Echo", "description": "Warm and confident"},
    {"id": "fable", "name": "Fable", "description": "British and expressive"},
    {"id": "onyx", "name": "Onyx", "description": "Deep and authoritative"},
    {"id": "nova", "name": "Nova", "description": "Young and bright"},
    {"id": "shimmer", "name": "Shimmer", "description": "Soft and gentle"},
]


# ---------------------------------------------------------------------------
# AudioService
# ---------------------------------------------------------------------------

class AudioService:
    """
    Reusable speech processing service.

    Usage::

        svc = AudioService()
        text = await svc.transcribe(db, user_id, audio_bytes, "en")
        audio = await svc.synthesize(db, user_id, "Hello world")
    """

    def _get_openai_api_key(self, db: Session, user_id: str) -> Optional[str]:
        """Extract OpenAI API key from user's model configurations."""
        try:
            from backend.models.entities import UserModelConfig
            configs = (
                db.query(UserModelConfig)
                .filter(
                    UserModelConfig.user_id == user_id,
                    UserModelConfig.is_active == True,  # noqa: E712
                    UserModelConfig.provider.in_(["openai", "OpenAI"]),
                )
                .all()
            )
            for cfg in configs:
                key = cfg.get_decrypted_api_key()
                if key:
                    return key
        except Exception as exc:
            logger.debug("Could not retrieve OpenAI key: %s", exc)
        return None

    def _get_openai_client(self, api_key: str):
        """Create an OpenAI client instance."""
        from openai import OpenAI
        return OpenAI(api_key=api_key)

    # ── Availability ─────────────────────────────────────────────────────

    def is_available(self, db: Session, user_id: str) -> bool:
        """Check if voice features are available (i.e. OpenAI key configured)."""
        return self._get_openai_api_key(db, user_id) is not None

    def get_status(self, db: Session, user_id: str) -> Dict[str, Any]:
        """Detailed availability status."""
        key = self._get_openai_api_key(db, user_id)
        return {
            "available": key is not None,
            "provider": "openai",
            "stt_model": "whisper-1",
            "tts_model": "tts-1",
            "voices": AVAILABLE_TTS_VOICES,
            "max_audio_size_mb": MAX_AUDIO_SIZE // (1024 * 1024),
        }

    # ── Speech-to-Text ───────────────────────────────────────────────────

    async def transcribe(
        self,
        db: Session,
        user_id: str,
        audio_bytes: bytes,
        language: Optional[str] = None,
        filename: str = "audio.wav",
    ) -> str:
        """
        Transcribe audio bytes to text using OpenAI Whisper.

        Args:
            db: Database session (for key lookup)
            user_id: User requesting transcription
            audio_bytes: Raw audio data
            language: Optional ISO-639-1 language code
            filename: Filename hint for format detection

        Returns:
            The transcribed text.

        Raises:
            ValueError: If no API key is configured or audio is too large.
        """
        api_key = self._get_openai_api_key(db, user_id)
        if not api_key:
            raise ValueError("No OpenAI API key configured for voice features")

        if len(audio_bytes) > MAX_AUDIO_SIZE:
            raise ValueError(
                f"Audio too large: {len(audio_bytes)} bytes "
                f"(max {MAX_AUDIO_SIZE} bytes)"
            )

        client = self._get_openai_client(api_key)

        # Write to temp file (Whisper requires a file-like object)
        suffix = Path(filename).suffix or ".wav"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            with open(tmp_path, "rb") as audio_file:
                kwargs: Dict[str, Any] = {
                    "model": "whisper-1",
                    "file": audio_file,
                }
                if language:
                    kwargs["language"] = language

                transcript = client.audio.transcriptions.create(**kwargs)
                return transcript.text
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    # ── Text-to-Speech ────────────────────────────────────────────────────

    async def synthesize(
        self,
        db: Session,
        user_id: str,
        text: str,
        voice: str = "alloy",
        speed: float = 1.0,
    ) -> bytes:
        """
        Synthesize text to speech using OpenAI TTS.

        Args:
            db: Database session (for key lookup)
            user_id: User requesting synthesis
            text: Text to convert to speech
            voice: TTS voice ID (alloy, echo, fable, onyx, nova, shimmer)
            speed: Speed multiplier (0.25 – 4.0)

        Returns:
            MP3 audio bytes.

        Raises:
            ValueError: If no API key is configured.
        """
        api_key = self._get_openai_api_key(db, user_id)
        if not api_key:
            raise ValueError("No OpenAI API key configured for voice features")

        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        # Clamp speed
        speed = max(0.25, min(4.0, speed))

        # Validate voice
        valid_voices = [v["id"] for v in AVAILABLE_TTS_VOICES]
        if voice not in valid_voices:
            voice = "alloy"

        client = self._get_openai_client(api_key)

        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text,
            speed=speed,
        )

        # Collect the audio bytes
        audio_data = b""
        for chunk in response.iter_bytes(chunk_size=4096):
            audio_data += chunk

        return audio_data

    # ── Voice List ─────────────────────────────────────────────────────────

    @staticmethod
    def get_available_voices() -> List[Dict[str, str]]:
        """Return list of available TTS voices."""
        return AVAILABLE_TTS_VOICES


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_audio_service: Optional[AudioService] = None


def get_audio_service() -> AudioService:
    """Return the singleton AudioService."""
    global _audio_service
    if _audio_service is None:
        _audio_service = AudioService()
    return _audio_service
