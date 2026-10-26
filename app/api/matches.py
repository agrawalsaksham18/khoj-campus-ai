import json
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from app.database import Database
from app.schemas import InterestRequest
from app.privacy import sanitize_report_for_public

router = APIRouter(prefix="/api/matches", tags=["matches"])

@router.get("", response_model=List[dict])
def list_matches(min_score: float = Query(35.0)):
    rows = Database.fetch_all("""
    SELECT m.*,
           lr.item_name as lost_item_name, lr.category as lost_category, lr.location as lost_location, lr.user_id as lost_user_id,
           fr.item_name as found_item_name, fr.category as found_category, fr.location as found_location, fr.user_id as found_user_id
    FROM matches m
    JOIN reports lr ON m.lost_report_id = lr.id
    JOIN reports fr ON m.found_report_id = fr.id
    WHERE m.match_score >= ?
    ORDER BY m.match_score DESC
    """, (min_score,))

    results = []
    for r in rows:
        item = dict(r)
        try:
            item["matching_reasons"] = json.loads(item["matching_reasons"])
        except Exception:
            item["matching_reasons"] = []
        results.append(item)
    return results

@router.get("/{match_id}")
def get_match(match_id: str):
    row = Database.fetch_one("SELECT * FROM matches WHERE id = ?", (match_id,))
    if not row:
        raise HTTPException(status_code=404, detail="Match record not found")

    lost_rep = Database.fetch_one("SELECT * FROM reports WHERE id = ?", (row["lost_report_id"],))
    found_rep = Database.fetch_one("SELECT * FROM reports WHERE id = ?", (row["found_report_id"],))

    match_dict = dict(row)
    try:
        match_dict["matching_reasons"] = json.loads(match_dict["matching_reasons"])
    except Exception:
        match_dict["matching_reasons"] = []

    match_dict["lost_report"] = sanitize_report_for_public(lost_rep) if lost_rep else None
    match_dict["found_report"] = sanitize_report_for_public(found_rep) if found_rep else None
    return match_dict

@router.post("/{match_id}/interest")
def express_interest(match_id: str, payload: InterestRequest):
    row = Database.fetch_one("SELECT * FROM matches WHERE id = ?", (match_id,))
    if not row:
        raise HTTPException(status_code=404, detail="Match not found")

    Database.execute("""
    UPDATE matches
    SET review_status = 'interested', claimant_notes = ?
    WHERE id = ?
    """, (payload.claimant_notes, match_id))

    # Mark both reports as 'matched' (in review), but NEVER automatically 'returned'
    Database.execute("UPDATE reports SET status = 'matched' WHERE id IN (?, ?) AND status = 'open'",
                     (row["lost_report_id"], row["found_report_id"]))

    return {
        "status": "success",
        "message": "Interest recorded! The finder will review your verification details to arrange safe collection.",
        "match_id": match_id
    }
