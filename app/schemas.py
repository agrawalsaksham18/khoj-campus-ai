from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field

class UserOut(BaseModel):
    id: str
    display_name: str
    email: str
    created_at: str

class ReportCreate(BaseModel):
    report_type: Literal['lost', 'found']
    item_name: str = Field(..., min_length=2, max_length=150)
    original_description: str = Field(..., min_length=5, max_length=2000)
    normalized_description: Optional[str] = None
    category: str = Field(..., description="Item category")
    color: Optional[str] = None
    brand: Optional[str] = None
    distinguishing_features: Optional[str] = None
    location: str = Field(..., min_length=2, max_length=200)
    occurrence_time: Optional[str] = None
    photo_url: Optional[str] = None
    preferred_language: Optional[str] = "en"
    user_id: Optional[str] = None
    is_demo: Optional[bool] = False

class ReportUpdate(BaseModel):
    item_name: Optional[str] = None
    category: Optional[str] = None
    color: Optional[str] = None
    brand: Optional[str] = None
    distinguishing_features: Optional[str] = None
    location: Optional[str] = None
    status: Optional[Literal['open', 'matched', 'returned', 'closed']] = None

class ReportOut(BaseModel):
    id: str
    user_id: str
    report_type: Literal['lost', 'found']
    item_name: str
    original_description: str
    normalized_description: Optional[str] = None
    category: str
    color: Optional[str] = None
    brand: Optional[str] = None
    distinguishing_features: Optional[str] = None
    location: str
    occurrence_time: Optional[str] = None
    photo_url: Optional[str] = None
    preferred_language: str
    status: Literal['open', 'matched', 'returned', 'closed']
    is_demo: bool
    created_at: str
    updated_at: str
    user_name: Optional[str] = None
    potential_matches_count: Optional[int] = 0

class MatchRecordOut(BaseModel):
    id: str
    lost_report_id: str
    found_report_id: str
    match_score: float
    matching_reasons: List[str]
    review_status: Literal['pending', 'interested', 'verified', 'rejected']
    claimant_notes: Optional[str] = None
    created_at: str
    lost_report: Optional[ReportOut] = None
    found_report: Optional[ReportOut] = None

class AIAnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=3, max_length=2000)
    preferred_language: Optional[str] = "unknown"

class AIAnalyzeResponse(BaseModel):
    item_type: Optional[str] = None
    category: Optional[str] = None
    color: Optional[str] = None
    brand: Optional[str] = None
    distinguishing_features: Optional[str] = None
    location: Optional[str] = None
    approximate_time: Optional[str] = None
    normalized_description: Optional[str] = None
    language_detected: Optional[str] = None
    is_ai_powered: bool = False
    notes: Optional[str] = None

class InterestRequest(BaseModel):
    claimant_notes: str = Field(..., min_length=5, max_length=1000, description="Verification details proving ownership")

class StatsOut(BaseModel):
    total_reports: int
    lost_count: int
    found_count: int
    matched_count: int
    returned_count: int
    campus: str
