"""
WebCall Arabic - FastAPI entrypoint and WebSocket transcription endpoint.
"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, Query, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .websocket_handler import WebSocketHandler, STORAGE_DIR
from .config import config
from .database import init_db, get_all_transcriptions, save_dictionary_profile, get_dictionary_profiles, delete_dictionary_profile

class ProfileCreate(BaseModel):
    name: str
    hotwords: List[Dict[str, Any]]
    replacements: List[Dict[str, str]]

# Logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    On startup: warn if Speechmatics API key is missing. Initialize DB.
    """
    if not (config.SPEECHMATICS_API_KEY or "").strip():
        logger.warning(
            "SPEECHMATICS_API_KEY is not set. Copy .env.example to .env at the repository root "
            "and set your key, or WebSocket transcription will fail. HTTP /health still works."
        )
    else:
        logger.info("Speechmatics API key is loaded.")
    
    init_db()
    logger.info("SQLite Database initialized.")
    yield


app = FastAPI(
    title="WebCall Arabic",
    description="Real-time speech-to-text service for Arabic with SQLite DB.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
@app.get("/health")
async def health_check():
    """Liveness probe."""
    return {"status": "healthy"}

@app.get("/api/history")
async def get_history():
    """Retrieve all transcription records."""
    records = get_all_transcriptions()
    return JSONResponse(content={"records": records})

@app.get("/api/download/{session_id}")
async def download_audio(session_id: str):
    """Download the saved wav file for a given session."""
    file_path = STORAGE_DIR / f"{session_id}.wav"
    if not file_path.exists():
        return JSONResponse(status_code=404, content={"error": "File not found"})
    return FileResponse(
        path=file_path, 
        filename=f"recording_{session_id}.wav",
        media_type="audio/wav"
    )

@app.get("/api/download_log/{session_id}")
async def download_log(session_id: str):
    """Download the saved log file for a given session."""
    file_path = STORAGE_DIR / f"{session_id}.log"
    if not file_path.exists():
        return JSONResponse(status_code=404, content={"error": "Log file not found"})
    return FileResponse(
        path=file_path, 
        filename=f"recording_{session_id}.log",
        media_type="text/plain"
    )

@app.get("/api/profiles")
async def list_profiles():
    """Retrieve all dictionary profiles."""
    profiles = get_dictionary_profiles()
    return JSONResponse(content={"profiles": profiles})

@app.post("/api/profiles")
async def create_profile(profile: ProfileCreate):
    """Create or update a dictionary profile."""
    try:
        save_dictionary_profile(profile.name, profile.hotwords, profile.replacements)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/profiles/{profile_id}")
async def delete_profile(profile_id: int):
    """Delete a dictionary profile."""
    try:
        delete_dictionary_profile(profile_id)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/transcribe")
async def websocket_endpoint(
    websocket: WebSocket,
    language: str = Query(default="ar", regex="^(ar|en|ar_en)$")
):
    """
    Real-time transcription WebSocket.

    Args:
        websocket: Browser or client WebSocket.
        language: ar, en, or ar_en.

    Frames:
        - Text JSON: {"action": "start", "hotwords": [...]} or {"action": "end"}
        - Binary: PCM s16le mono 16 kHz chunks
    """
    logger.info(f"New WebSocket connection request with language={language}")

    handler = WebSocketHandler(websocket, language)
    await handler.handle()


if __name__ == "__main__":
    import uvicorn

    try:
        config.validate()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        exit(1)

    logger.info(f"Starting server on {config.HOST}:{config.PORT}")
    uvicorn.run(
        "backend.main:app",
        host=config.HOST,
        port=config.PORT,
        reload=True,
        log_level="info"
    )
