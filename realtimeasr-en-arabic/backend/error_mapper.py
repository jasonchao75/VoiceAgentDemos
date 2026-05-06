"""
Error code mapping: internal errors to user-facing English messages.
"""
from enum import Enum


class ErrorCode(str, Enum):
    """Error code identifiers."""
    TIMEOUT = "TIMEOUT"
    CONNECTION_LOST = "CONNECTION_LOST"
    INVALID_AUDIO = "INVALID_AUDIO"
    MAX_DURATION_EXCEEDED = "MAX_DURATION_EXCEEDED"
    TRANSCRIPTION_SERVICE = "TRANSCRIPTION_SERVICE"
    INTERNAL_ERROR = "INTERNAL_ERROR"


# User-visible messages (English only)
ERROR_MESSAGES = {
    ErrorCode.TIMEOUT: "Connection timeout. Please try again.",
    ErrorCode.CONNECTION_LOST: "Connection lost. Please check your network.",
    ErrorCode.INVALID_AUDIO: "Invalid audio format. Please check your microphone settings.",
    ErrorCode.MAX_DURATION_EXCEEDED: "Maximum duration of 2 minutes exceeded. Session ended.",
    ErrorCode.TRANSCRIPTION_SERVICE: (
        "Cannot connect to the transcription service. "
        "Please check your network connection and server configuration."
    ),
    ErrorCode.INTERNAL_ERROR: "An internal error occurred. Please try again later.",
}


def create_error_message(error_code: ErrorCode, details: str = "") -> dict:
    """
    Build a JSON-serializable error payload for the client.

    Args:
        error_code: Which error to surface.
        details: Optional internal detail (not sent to the client).

    Returns:
        Dict with type, code, and message.
    """
    return {
        "type": "error",
        "code": error_code.value,
        "message": ERROR_MESSAGES[error_code]
    }
