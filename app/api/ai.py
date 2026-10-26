from fastapi import APIRouter
from app.schemas import AIAnalyzeRequest, AIAnalyzeResponse
from app.sarvam_service import sarvam_service
from app.config import settings

router = APIRouter(prefix="/api/ai", tags=["ai"])

@router.post("/analyze", response_model=AIAnalyzeResponse)
def analyze_report_text(payload: AIAnalyzeRequest):
    """
    Extracts structured attributes from Hindi, Hinglish, or English descriptions.
    Uses Sarvam AI 105B when API key is set; fallback to heuristic parser otherwise.
    """
    return sarvam_service.analyze_description(
        text=payload.text,
        preferred_lang=payload.preferred_language
    )

@router.get("/status")
def get_ai_status():
    """
    Returns the operational status of the Sarvam AI integration.
    """
    return {
        "sarvam_api_key_configured": settings.has_sarvam_key,
        "mode": "Sarvam 105B & Saaras Speech-to-Text" if settings.has_sarvam_key else "Offline Heuristic Mode (Ready for SARVAM_API_KEY)",
        "models_supported": ["sarvam-105b", "sarvam-105b-conversations", "saaras:v4"],
        "college": settings.COLLEGE_NAME
    }
