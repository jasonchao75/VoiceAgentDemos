"""
Speechmatics Realtime API WebSocket client.
"""
import json
import asyncio
import logging
import re
from typing import Optional, Callable
import websockets
from websockets.client import WebSocketClientProtocol

from .config import config
from .error_mapper import ErrorCode, create_error_message

logger = logging.getLogger(__name__)


def _speechmatics_transcription_language(language: str) -> str:
    """Map app codes to Speechmatics language; must match the /v2/{lang} URL segment."""
    # ar_en is the bilingual Arabic-English realtime model (not plain "ar").
    return {"ar": "ar", "en": "en", "ar_en": "ar_en"}.get(language, language)


def _speechmatics_connect_url(base_url: str, language: str) -> str:
    """
    Speechmatics requires the language in the WebSocket path to match
    transcription_config.language in StartRecognition.
    """
    base = (base_url or "").strip().rstrip("/")
    url_lang = _speechmatics_transcription_language(language)
    m = re.search(r"^(.*)/v2/([^/]+)$", base, flags=re.IGNORECASE)
    if m:
        prefix = m.group(1).rstrip("/")
        return f"{prefix}/v2/{url_lang}"
    if base.lower().endswith("/v2"):
        return f"{base}/{url_lang}"
    return base


class SpeechmaticsClient:
    """Upstream realtime transcription session."""

    def __init__(self, language: str = "ar", hotwords: list = None):
        """
        Args:
            language: ar, en, or ar_en.
            hotwords: additional_vocab list for Speechmatics
        """
        self.language = language
        self.hotwords = hotwords or []
        self.ws: Optional[WebSocketClientProtocol] = None
        self.session_id: Optional[str] = None
        self._message_handler: Optional[Callable] = None

    async def connect(self, message_handler: Callable) -> str:
        """
        Open Speechmatics WebSocket and wait for RecognitionStarted.

        Args:
            message_handler: async callable receiving client-shaped dicts.

        Returns:
            session_id from Speechmatics.

        Raises:
            Exception: handshake or config rejected.
        """
        self._message_handler = message_handler

        try:
            connect_uri = _speechmatics_connect_url(config.SPEECHMATICS_URL, self.language)
            logger.info("Speechmatics WebSocket URI: %s", connect_uri)
            self.ws = await asyncio.wait_for(
                websockets.connect(
                    connect_uri,
                    extra_headers={"Authorization": f"Bearer {config.SPEECHMATICS_API_KEY}"},
                ),
                timeout=10.0,
            )

            logger.info(f"Connected to Speechmatics with language={self.language}")

            start_recognition = {
                "message": "StartRecognition",
                "audio_format": {
                    "type": "raw",
                    "encoding": "pcm_s16le",
                    "sample_rate": 16000
                },
                "transcription_config": {
                    "language": _speechmatics_transcription_language(self.language),
                    "diarization": "speaker",
                    "enable_partials": True,
                },
            }

            if self.hotwords and len(self.hotwords) > 0:
                start_recognition["transcription_config"]["additional_vocab"] = self.hotwords

            await self.ws.send(json.dumps(start_recognition))
            logger.info(f"Sent StartRecognition with hotwords: {self.hotwords}")

            max_attempts = 3
            for attempt in range(max_attempts):
                response = await asyncio.wait_for(self.ws.recv(), timeout=5.0)
                response_data = json.loads(response)
                message_type = response_data.get("message")

                if message_type == "RecognitionStarted":
                    self.session_id = response_data.get("id", "unknown")
                    logger.info(f"Recognition started, session_id={self.session_id}")
                    return self.session_id
                elif message_type == "Info":
                    logger.info(f"Received Info message: {response_data.get('type')}")
                    continue
                elif message_type == "Error":
                    error_type = response_data.get("type", "unknown")
                    reason = response_data.get("reason", "unknown")
                    raise Exception(f"Speechmatics error: {error_type} - {reason}")
                else:
                    logger.warning(f"Unexpected message: {message_type}")
                    continue

            raise Exception("Did not receive RecognitionStarted message")

        except asyncio.TimeoutError:
            logger.error("Connection timeout")
            raise Exception("TIMEOUT")
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            raise

    async def send_audio(self, audio_data: bytes):
        """
        Send one PCM chunk (binary AddAudio).

        Args:
            audio_data: Raw s16le mono 16 kHz bytes.
        """
        if not self.ws:
            raise Exception("Not connected")

        try:
            await self.ws.send(audio_data)
        except Exception as e:
            logger.error(f"Failed to send audio: {e}")
            raise

    async def end_stream(self):
        """Send EndOfStream JSON."""
        if not self.ws:
            return

        try:
            end_of_stream = {"message": "EndOfStream"}
            await self.ws.send(json.dumps(end_of_stream))
            logger.info("Sent EndOfStream")
        except Exception as e:
            logger.error(f"Failed to send EndOfStream: {e}")

    async def listen(self):
        """Pump Speechmatics messages until the connection closes."""
        if not self.ws or not self._message_handler:
            return

        try:
            async for message in self.ws:
                try:
                    data = json.loads(message)
                    await self._handle_speechmatics_message(data)
                except json.JSONDecodeError:
                    logger.warning("Received non-JSON message")
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
        except websockets.exceptions.ConnectionClosed:
            logger.info("Speechmatics connection closed")
        except Exception as e:
            logger.error(f"Listen error: {e}")

    async def _handle_speechmatics_message(self, data: dict):
        """
        Map Speechmatics payloads to the browser contract.

        Args:
            data: Parsed JSON from Speechmatics.
        """
        message_type = data.get("message")

        logger.debug(f"Received Speechmatics message: {message_type}")
        if message_type in ["AddPartialTranscript", "AddTranscript"]:
            logger.debug(f"Full message data: {json.dumps(data, ensure_ascii=False)}")

        if message_type == "AddPartialTranscript":
            metadata = data.get("metadata", {})
            transcript = metadata.get("transcript", "").strip()

            if not transcript:
                return

            results = data.get("results", [])
            speaker = "S1"
            if results and len(results) > 0:
                alternatives = results[0].get("alternatives", [])
                if alternatives and len(alternatives) > 0:
                    items = alternatives[0].get("items", [])
                    if items and len(items) > 0:
                        speaker = items[0].get("speaker", "S1")

            client_message = {
                "type": "partial",
                "text": transcript,
                "speaker": speaker
            }
            await self._message_handler(client_message)

        elif message_type == "AddTranscript":
            metadata = data.get("metadata", {})
            transcript = metadata.get("transcript", "").strip()

            if not transcript:
                return

            results = data.get("results", [])
            speaker = "S1"
            if results and len(results) > 0:
                alternatives = results[0].get("alternatives", [])
                if alternatives and len(alternatives) > 0:
                    items = alternatives[0].get("items", [])
                    if items and len(items) > 0:
                        speaker = items[0].get("speaker", "S1")

            client_message = {
                "type": "final",
                "text": transcript,
                "speaker": speaker
            }
            await self._message_handler(client_message)

        elif message_type == "EndOfTranscript":
            logger.info("Received EndOfTranscript")

        elif message_type == "Error":
            error_type = data.get("type", "unknown")
            logger.error(f"Speechmatics error: {error_type}")
            error_message = create_error_message(ErrorCode.INTERNAL_ERROR)
            await self._message_handler(error_message)

    async def close(self):
        """Close upstream WebSocket."""
        if self.ws:
            try:
                await self.ws.close()
                logger.info("Speechmatics connection closed")
            except Exception as e:
                logger.error(f"Error closing connection: {e}")
            finally:
                self.ws = None
