"""
Load application configuration from environment variables.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from repo root and backend/ (uvicorn cwd may be backend/)
_backend_dir = Path(__file__).resolve().parent
_repo_root = _backend_dir.parent
# override=False: process env (e.g. K8s) wins; .env only fills keys that are not already set
if (_repo_root / ".env").is_file():
    load_dotenv(_repo_root / ".env", override=False)
if (_backend_dir / ".env").is_file():
    load_dotenv(_backend_dir / ".env", override=False)


class Config:
    """Runtime configuration."""

    # Speechmatics (trim key to avoid stray whitespace/BOM from editors)
    SPEECHMATICS_API_KEY: str = (os.getenv("SPEECHMATICS_API_KEY") or "").strip().lstrip("\ufeff")
    # Base URL may end at /v2; speechmatics_client appends /{lang} per session (per Speechmatics docs)
    SPEECHMATICS_URL: str = (os.getenv("SPEECHMATICS_URL") or "wss://eu2.rt.speechmatics.com/v2").strip()

    # HTTP server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8010"))

    # Session limits
    MAX_DURATION_SECONDS: int = 120  # 2 minutes

    @classmethod
    def validate(cls):
        """Require SPEECHMATICS_API_KEY when starting via python -m backend.main."""
        if not cls.SPEECHMATICS_API_KEY:
            raise ValueError(
                "SPEECHMATICS_API_KEY is required (set in environment or in .env at repo root / backend/)"
            )


config = Config()
