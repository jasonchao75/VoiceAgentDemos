"""
Speechmatics Realtime API WebSocket client.
"""

import json
import asyncio
import logging
import ssl
from typing import Optional, Callable
import websockets
from websockets.client import WebSocketClientProtocol

from .config import config
from .error_mapper import ErrorCode, create_error_message

logger = logging.getLogger(__name__)


def _speechmatics_transcription_language(language: str) -> str:
    """Map app language codes to Speechmatics transcription_config.language."""
    # ar_en is the bilingual Arabic-English realtime model (not plain "ar").
    return {"ar": "ar", "en": "en", "ar_en": "ar_en"}.get(language, language)


def _speechmatics_connect_url(base_url: str) -> str:
    """Normalize the configured Speechmatics Realtime /v2 WebSocket URL."""
    base = (base_url or "").strip().rstrip("/")
    return base


class SpeechmaticsClient:
    """Upstream realtime transcription session."""

    def __init__(
        self,
        language: str = "ar",
        hotwords: list = None,
        replacements: list = None,
        log_callback: Callable = None,
        sample_rate: int = 16000,
    ):
        """
        Args:
            language: ar, en, or ar_en.
            hotwords: additional_vocab list for Speechmatics
            replacements: custom transcript replacements
            log_callback: callback for custom session logging
            sample_rate: 8000 or 16000
        """
        self.language = language
        self.hotwords = hotwords or []
        self.replacements = replacements or []
        self.log_callback = log_callback
        self.sample_rate = sample_rate
        self.audio_seq_no = 0
        self.end_of_transcript_received = False
        self._end_of_transcript_event = asyncio.Event()

    def _write_log(self, msg: str):
        if self.log_callback:
            self.log_callback(msg)

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
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            connect_uri = _speechmatics_connect_url(config.SPEECHMATICS_URL)
            logger.info("Speechmatics WebSocket URI: %s", connect_uri)
            self._write_log(f"Connecting to {connect_uri}")
            self.ws = await asyncio.wait_for(
                websockets.connect(
                    connect_uri,
                    additional_headers={
                        "Authorization": f"Bearer {config.SPEECHMATICS_API_KEY}"
                    },
                    ssl=ssl_context,
                ),
                timeout=10.0,
            )

            logger.info(f"Connected to Speechmatics with language={self.language}")

            start_recognition = {
                "message": "StartRecognition",
                "audio_format": {
                    "type": "raw",
                    "encoding": "pcm_s16le",
                    "sample_rate": self.sample_rate,
                },
                "transcription_config": {
                    "language": _speechmatics_transcription_language(self.language),
                    "diarization": "speaker",
                    "enable_partials": True,
                },
            }

            if self.hotwords and len(self.hotwords) > 0:
                start_recognition["transcription_config"]["additional_vocab"] = (
                    self.hotwords
                )

            if self.replacements and len(self.replacements) > 0:
                start_recognition["transcription_config"][
                    "transcript_filtering_config"
                ] = {"remove_disfluencies": False, "replacements": self.replacements}

            start_json_str = json.dumps(start_recognition)
            self._write_log(f"Sending StartRecognition: {start_json_str}")
            await self.ws.send(start_json_str)
            logger.info(f"Sent StartRecognition with hotwords: {self.hotwords}")

            max_attempts = 3
            for attempt in range(max_attempts):
                response = await asyncio.wait_for(self.ws.recv(), timeout=5.0)
                response_data = json.loads(response)
                message_type = response_data.get("message")

                if message_type == "RecognitionStarted":
                    self.session_id = response_data.get("id", "unknown")
                    logger.info(f"Recognition started, session_id={self.session_id}")
                    self._write_log("Received RecognitionStarted from server.")
                    self._write_log("Starting to send audio data...")
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
            self.audio_seq_no += 1
        except Exception as e:
            logger.error(f"Failed to send audio: {e}")
            raise

    async def end_stream(self):
        """Send EndOfStream JSON."""
        if not self.ws:
            return

        try:
            end_of_stream = {
                "message": "EndOfStream",
                "last_seq_no": self.audio_seq_no,
            }
            await self.ws.send(json.dumps(end_of_stream))
            logger.info("Sent EndOfStream with last_seq_no=%s", self.audio_seq_no)
        except Exception as e:
            logger.error(f"Failed to send EndOfStream: {e}")
            self._end_of_transcript_event.set()

    async def wait_for_end_of_transcript(self, timeout: float = 10.0) -> bool:
        """Wait until Speechmatics confirms all final transcripts were emitted."""
        try:
            await asyncio.wait_for(
                self._end_of_transcript_event.wait(), timeout=timeout
            )
            return self.end_of_transcript_received
        except asyncio.TimeoutError:
            logger.warning("Timed out waiting for EndOfTranscript")
            return False

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
        finally:
            self._end_of_transcript_event.set()

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

            self._write_log(f"[Partial]: {transcript}")

            results = data.get("results", [])
            speaker = "S1"
            if results and len(results) > 0:
                alternatives = results[0].get("alternatives", [])
                if alternatives and len(alternatives) > 0:
                    items = alternatives[0].get("items", [])
                    if items and len(items) > 0:
                        speaker = items[0].get("speaker", "S1")

            client_message = {"type": "partial", "text": transcript, "speaker": speaker}
            await self._message_handler(client_message)

        elif message_type == "AddTranscript":
            metadata = data.get("metadata", {})
            transcript = metadata.get("transcript", "").strip()

            if not transcript:
                return

            self._write_log(f"[Final]: {transcript}")

            results = data.get("results", [])
            speaker = "S1"
            if results and len(results) > 0:
                alternatives = results[0].get("alternatives", [])
                if alternatives and len(alternatives) > 0:
                    items = alternatives[0].get("items", [])
                    if items and len(items) > 0:
                        speaker = items[0].get("speaker", "S1")

            client_message = {"type": "final", "text": transcript, "speaker": speaker}
            await self._message_handler(client_message)

        elif message_type == "EndOfTranscript":
            logger.info("Received EndOfTranscript")
            self.end_of_transcript_received = True
            self._write_log("Received EndOfTranscript from server.")
            self._end_of_transcript_event.set()

        elif message_type == "Error":
            error_type = data.get("type", "unknown")
            logger.error(f"Speechmatics error: {error_type}")
            error_message = create_error_message(ErrorCode.INTERNAL_ERROR)
            await self._message_handler(error_message)
            self._end_of_transcript_event.set()

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
