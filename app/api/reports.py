import uuid
import json
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form
from app.database import Database
from app.schemas import ReportCreate, ReportUpdate, ReportOut
from app.privacy import sanitize_report_for_public
from app.matching_engine import sync_all_matches, find_matches_for_report
from app.sarvam_service import sarvam_service

router = APIRouter(prefix="/api/reports", tags=["reports"])

@router.get("", response_model=List[dict])
def list_reports(
    report_type: Optional[str] = Query(None, description="lost, found, or all"),
    category: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    sort: Optional[str] = Query("newest"),
    is_demo: Optional[bool] = Query(None)
):
    query = """
    SELECT r.*, u.display_name as user_name,
           (SELECT COUNT(*) FROM matches m WHERE m.lost_report_id = r.id OR m.found_report_id = r.id) as potential_matches_count
    FROM reports r
    JOIN users u ON r.user_id = u.id
    WHERE 1=1
    """
    params = []

    if report_type and report_type.lower() != "all":
        query += " AND r.report_type = ?"
        params.append(report_type.lower())

    if category and category.lower() != "all":
        query += " AND r.category = ?"
        params.append(category.lower())

    if location and location.lower() != "all":
        query += " AND r.location LIKE ?"
        params.append(f"%{location}%")

    if status and status.lower() != "all":
        query += " AND r.status = ?"
        params.append(status.lower())

    if is_demo is not None:
        query += " AND r.is_demo = ?"
        params.append(1 if is_demo else 0)

    if search and search.strip():
        term = f"%{search.strip().lower()}%"
        query += " AND (LOWER(r.item_name) LIKE ? OR LOWER(r.original_description) LIKE ? OR LOWER(r.distinguishing_features) LIKE ? OR LOWER(r.location) LIKE ?)"
        params.extend([term, term, term, term])

    if sort == "oldest":
        query += " ORDER BY r.created_at ASC"
    else:
        query += " ORDER BY r.created_at DESC"

    rows = Database.fetch_all(query, tuple(params))
    # Sanitize each report for public viewing (mask sensitive phone numbers, roll numbers, IDs)
    return [sanitize_report_for_public(r) for r in rows]

@router.get("/my-reports")
def get_my_reports(user_id: str = Query("usr_aarav")):
    rows = Database.fetch_all("""
    SELECT r.*, u.display_name as user_name,
           (SELECT COUNT(*) FROM matches m WHERE m.lost_report_id = r.id OR m.found_report_id = r.id) as potential_matches_count
    FROM reports r
    JOIN users u ON r.user_id = u.id
    WHERE r.user_id = ?
    ORDER BY r.created_at DESC
    """, (user_id,))
    return rows

@router.get("/{report_id}")
def get_report(report_id: str):
    row = Database.fetch_one("""
    SELECT r.*, u.display_name as user_name,
           (SELECT COUNT(*) FROM matches m WHERE m.lost_report_id = r.id OR m.found_report_id = r.id) as potential_matches_count
    FROM reports r
    JOIN users u ON r.user_id = u.id
    WHERE r.id = ?
    """, (report_id,))
    if not row:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Get ranked candidate matches for this report
    candidates = find_matches_for_report(report_id)
    sanitized = sanitize_report_for_public(row)
    sanitized["candidate_matches"] = candidates
    return sanitized

@router.post("", response_model=dict, status_code=201)
def create_report(payload: ReportCreate):
    now = datetime.now(timezone.utc).isoformat()
    report_id = f"rep_{uuid.uuid4().hex[:10]}"

    # Fallback default user if not provided
    user_id = payload.user_id or "usr_aarav"
    # Ensure user exists
    user = Database.fetch_one("SELECT id FROM users WHERE id = ?", (user_id,))
    if not user:
        Database.execute("INSERT OR IGNORE INTO users (id, display_name, email, created_at) VALUES (?, ?, ?, ?)",
                         (user_id, "Campus Student", f"{user_id}@iitk.ac.in", now))

    # If normalized description or fields need enrichment, use Sarvam Service
    normalized_desc = payload.normalized_description
    if not normalized_desc:
        analysis = sarvam_service.analyze_description(payload.original_description, payload.preferred_language)
        normalized_desc = analysis.normalized_description or payload.original_description[:150]

    Database.execute("""
    INSERT INTO reports (
        id, user_id, report_type, item_name, original_description,
        normalized_description, category, color, brand,
        distinguishing_features, location, occurrence_time,
        photo_url, preferred_language, status, is_demo,
        created_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', ?, ?, ?)
    """, (
        report_id,
        user_id,
        payload.report_type,
        payload.item_name,
        payload.original_description,
        normalized_desc,
        payload.category,
        payload.color,
        payload.brand,
        payload.distinguishing_features,
        payload.location,
        payload.occurrence_time,
        payload.photo_url,
        payload.preferred_language or "en",
        1 if payload.is_demo else 0,
        now,
        now
    ))

    # Automatically recompute and sync matches in background
    sync_all_matches()

    created = Database.fetch_one("SELECT * FROM reports WHERE id = ?", (report_id,))
    return sanitize_report_for_public(created)

@router.patch("/{report_id}")
def update_report(report_id: str, payload: ReportUpdate):
    existing = Database.fetch_one("SELECT * FROM reports WHERE id = ?", (report_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Report not found")

    updates = []
    params = []
    now = datetime.now(timezone.utc).isoformat()

    if payload.item_name is not None:
        updates.append("item_name = ?")
        params.append(payload.item_name)
    if payload.category is not None:
        updates.append("category = ?")
        params.append(payload.category)
    if payload.color is not None:
        updates.append("color = ?")
        params.append(payload.color)
    if payload.brand is not None:
        updates.append("brand = ?")
        params.append(payload.brand)
    if payload.distinguishing_features is not None:
        updates.append("distinguishing_features = ?")
        params.append(payload.distinguishing_features)
    if payload.location is not None:
        updates.append("location = ?")
        params.append(payload.location)
    if payload.status is not None:
        updates.append("status = ?")
        params.append(payload.status)

    if not updates:
        return existing

    updates.append("updated_at = ?")
    params.append(now)
    params.append(report_id)

    query = f"UPDATE reports SET {', '.join(updates)} WHERE id = ?"
    Database.execute(query, tuple(params))

    # Re-sync matches if status changed
    sync_all_matches()

    updated = Database.fetch_one("SELECT * FROM reports WHERE id = ?", (report_id,))
    return sanitize_report_for_public(updated)

@router.delete("/{report_id}")
def delete_report(report_id: str):
    existing = Database.fetch_one("SELECT * FROM reports WHERE id = ?", (report_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Report not found")

    Database.execute("DELETE FROM reports WHERE id = ?", (report_id,))
    return {"message": "Report deleted successfully", "id": report_id}
