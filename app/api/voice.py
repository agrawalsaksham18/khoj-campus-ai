import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.sarvam_service import sarvam_service
from app.config import settings

logger = logging.getLogger("khoj.voice")
router = APIRouter(prefix="/api/voice", tags=["voice"])

@router.post("/transcribe")
async def transcribe_voice(file: UploadFile = File(...)):
    """
    Transcribes audio recorded from the user's browser or uploaded as a voice note.
    Powered by Sarvam AI Saaras:v4 Speech-to-Text.
    """
    if not settings.has_sarvam_key:
        raise HTTPException(
            status_code=503,
            detail="Sarvam AI API key is not configured. Please add your SARVAM_API_KEY to the .env file to enable Voice Speech-to-Text."
        )

    # Check file size (limit to 10MB)
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Audio file too large. Max size is 10MB.")

    try:
        transcript, lang = sarvam_service.transcribe_audio(
            audio_bytes=contents,
            filename=file.filename or "recording.webm",
            mime_type=file.content_type or "audio/webm"
        )
        return {
            "status": "success",
            "transcript": transcript,
            "detected_language": lang,
            "filename": file.filename
        }
    except Exception as e:
        logger.error(f"Voice transcription failed: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription error: {str(e)}")
