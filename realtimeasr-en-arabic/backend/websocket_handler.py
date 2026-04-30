"""
WebSocket handler: client session lifecycle and Speechmatics bridge.
"""
import json
import asyncio
import logging
import wave
import datetime
from pathlib import Path
from typing import Optional
from fastapi import WebSocket

from .speechmatics_client import SpeechmaticsClient
from .error_mapper import ErrorCode, create_error_message
from .config import config
from .database import save_transcription

logger = logging.getLogger(__name__)
STORAGE_DIR = Path(__file__).parent / "storage"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


class WebSocketHandler:
    """One client WebSocket plus upstream Speechmatics session."""

    def __init__(self, websocket: WebSocket, language: str):
        """
        Args:
            websocket: FastAPI WebSocket.
            language: ar, en, or ar_en.
        """
        self.websocket = websocket
        self.language = language
        self.speechmatics_client: Optional[SpeechmaticsClient] = None
        self.timeout_task: Optional[asyncio.Task] = None
        self.listen_task: Optional[asyncio.Task] = None
        self.is_active = False
        self.session_id = None
        self.raw_file = None
        self.raw_path = None
        self.final_transcript = []
        self.log_buffer = []

    async def handle(self):
        """Accept client, wait for start, connect upstream, relay until close."""
        try:
            await self.websocket.accept()
            logger.info(f"WebSocket connected with language={self.language}")

            if not (config.SPEECHMATICS_API_KEY or "").strip():
                logger.warning("Rejecting transcription: SPEECHMATICS_API_KEY is empty")
                await self._send_error(ErrorCode.TRANSCRIPTION_SERVICE)
                return

            # Wait for action="start" message before connecting to Speechmatics
            start_msg = await self.websocket.receive()
            if "text" not in start_msg:
                logger.error("First message must be JSON action='start'")
                await self._send_error(ErrorCode.INTERNAL_ERROR)
                return
            
            try:
                start_data = json.loads(start_msg["text"])
                if start_data.get("action") != "start":
                    raise ValueError("Not a start action")
                hotwords = start_data.get("hotwords", [])
                replacements = start_data.get("replacements", [])
            except Exception as e:
                logger.error(f"Failed to parse start message: {e}")
                await self._send_error(ErrorCode.INTERNAL_ERROR)
                return

            logger.info(f"Attempting to connect to Speechmatics with hotwords={hotwords}, replacements={replacements}")
            
            def session_logger(msg):
                now = datetime.datetime.now()
                formatted = f"{now.strftime('%Y-%m-%d %H:%M:%S')},{now.strftime('%f')[:3]} - INFO - {msg}\n"
                self.log_buffer.append(formatted)

            self.speechmatics_client = SpeechmaticsClient(language=self.language, hotwords=hotwords, replacements=replacements, log_callback=session_logger)

            try:
                self.session_id = await self.speechmatics_client.connect(self._send_to_client)
                logger.info(f"Successfully connected to Speechmatics, session_id={self.session_id}")
            except Exception as conn_error:
                logger.error(f"Failed to connect to Speechmatics: {conn_error}", exc_info=True)
                if "TIMEOUT" in str(conn_error):
                    await self._send_error(ErrorCode.TIMEOUT)
                else:
                    await self._send_error(ErrorCode.TRANSCRIPTION_SERVICE)
                return

            # Open raw file for audio persistence
            self.raw_path = STORAGE_DIR / f"{self.session_id}.raw"
            self.raw_file = open(self.raw_path, "wb")

            await self._send_to_client({
                "type": "session_started",
                "session_id": self.session_id,
                "language": self.language
            })

            self.is_active = True
            self.listen_task = asyncio.create_task(self.speechmatics_client.listen())
            self.timeout_task = asyncio.create_task(self._enforce_timeout())

            await self._handle_client_messages()

        except Exception as e:
            logger.error(f"WebSocket handler error: {e}", exc_info=True)
            if "TIMEOUT" in str(e):
                await self._send_error(ErrorCode.TIMEOUT)
            else:
                await self._send_error(ErrorCode.INTERNAL_ERROR)
        finally:
            await self._cleanup()

    async def _handle_client_messages(self):
        """Read client text/binary and forward audio upstream."""
        try:
            while self.is_active:
                message = await self.websocket.receive()

                if "text" in message:
                    await self._handle_text_message(message["text"])
                elif "bytes" in message:
                    await self._handle_binary_message(message["bytes"])

        except Exception as e:
            logger.error(f"Error handling client messages: {e}")
            if self.is_active:
                await self._send_error(ErrorCode.CONNECTION_LOST)

    async def _handle_text_message(self, text: str):
        """JSON control messages from the client."""
        try:
            data = json.loads(text)
            action = data.get("action")

            if action == "start":
                logger.warning("Received start action again, ignoring.")

            elif action == "end":
                logger.info("Received end action")
                if self.speechmatics_client:
                    await self.speechmatics_client.end_stream()
                    received_end = await self.speechmatics_client.wait_for_end_of_transcript()
                    if not received_end:
                        logger.warning("Proceeding without EndOfTranscript confirmation")
                self.is_active = False

            else:
                logger.warning(f"Unknown action: {action}")

        except json.JSONDecodeError:
            logger.error("Invalid JSON in text message")
        except Exception as e:
            logger.error(f"Error handling text message: {e}")

    async def _handle_binary_message(self, audio_data: bytes):
        """PCM frames from the client."""
        try:
            if self.speechmatics_client:
                await self.speechmatics_client.send_audio(audio_data)
            if self.raw_file:
                self.raw_file.write(audio_data)
        except Exception as e:
            logger.error(f"Error handling binary message: {e}")
            await self._send_error(ErrorCode.INVALID_AUDIO)

    async def _send_to_client(self, message: dict):
        """Send one JSON text frame to the client. Intercept finals for DB."""
        if message.get("type") == "final":
            text = message.get("text", "").strip()
            if text:
                self.final_transcript.append(text)
        
        try:
            await self.websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending to client: {e}")

    async def _send_error(self, error_code: ErrorCode):
        """Send standardized error payload."""
        error_message = create_error_message(error_code)
        await self._send_to_client(error_message)

    async def _enforce_timeout(self):
        """End session after MAX_DURATION_SECONDS."""
        try:
            await asyncio.sleep(config.MAX_DURATION_SECONDS)
            logger.info("Max duration exceeded, closing connection")
            await self._send_error(ErrorCode.MAX_DURATION_EXCEEDED)
            self.is_active = False
        except asyncio.CancelledError:
            pass

    async def _convert_and_save(self):
        """Convert raw PCM to WAV and save transcript to DB."""
        if not self.session_id or not self.raw_path or not self.raw_path.exists():
            return
        
        try:
            wav_path = STORAGE_DIR / f"{self.session_id}.wav"
            with open(self.raw_path, "rb") as f_raw:
                pcm_data = f_raw.read()
            with wave.open(str(wav_path), "wb") as f_wav:
                f_wav.setnchannels(1)
                f_wav.setsampwidth(2)
                f_wav.setframerate(16000)
                f_wav.writeframes(pcm_data)
            
            # Clean up raw file
            self.raw_path.unlink()
            
            # Save logs to file
            if self.session_id and self.log_buffer:
                log_path = STORAGE_DIR / f"{self.session_id}.log"
                with open(log_path, "w", encoding="utf-8") as f_log:
                    f_log.writelines(self.log_buffer)

            final_text = " ".join(self.final_transcript)
            save_transcription(
                session_id=self.session_id,
                language=self.language,
                final_transcript=final_text,
                audio_file_path=str(wav_path)
            )
            logger.info(f"Saved transcription to DB for {self.session_id}")
            
            await self._send_to_client({
                "type": "saved",
                "session_id": self.session_id,
                "download_url": f"/api/download/{self.session_id}"
            })
                
        except Exception as e:
            logger.error(f"Failed to convert/save audio: {e}")

    async def _cleanup(self):
        """Cancel tasks and close upstream/downstream sockets."""
        logger.info("Cleaning up resources")

        if self.raw_file:
            self.raw_file.close()
            await self._convert_and_save()

        if self.timeout_task and not self.timeout_task.done():
            self.timeout_task.cancel()
            try:
                await self.timeout_task
            except asyncio.CancelledError:
                pass

        if self.listen_task and not self.listen_task.done():
            self.listen_task.cancel()
            try:
                await self.listen_task
            except asyncio.CancelledError:
                pass

        if self.speechmatics_client:
            await self.speechmatics_client.close()

        try:
            await self.websocket.close()
        except Exception:
            pass

        logger.info("Cleanup completed")
