import os
import shutil
import uuid
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings, BASE_DIR
from app.database import init_db, Database
from app.demo_data import seed_demo_data, reset_demo_data
from app.matching_engine import sync_all_matches
from app.schemas import StatsOut

# API Routers
from app.api.reports import router as reports_router
from app.api.matches import router as matches_router
from app.api.ai import router as ai_router
from app.api.voice import router as voice_router

# Initialize SQLite database schema
init_db()
count = Database.fetch_one("SELECT COUNT(*) as c FROM reports")
if count and count["c"] == 0:
    seed_demo_data()

app = FastAPI(
    title="Khoj — AI Lost & Found Platform",
    description="Multilingual Lost & Found platform for IIT Kanpur powered by Sarvam AI",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(reports_router)
app.include_router(matches_router)
app.include_router(ai_router)
app.include_router(voice_router)

# Mount static files
static_dir = BASE_DIR / "app" / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Photo upload endpoint with strict file validation
@app.post("/api/upload")
async def upload_image(file: UploadFile = File(...)):
    allowed_types = {"image/jpeg", "image/png", "image/webp", "image/jpg"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{file.content_type}'. Only JPEG, PNG, and WebP images are allowed."
        )

    # Check file size (max 5MB)
    contents = await file.read()
    max_bytes = settings.MAX_IMAGE_UPLOAD_MB * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum allowed size of {settings.MAX_IMAGE_UPLOAD_MB}MB."
        )

    # Generate safe random filename
    ext = Path(file.filename).suffix or ".jpg"
    safe_filename = f"{uuid.uuid4().hex[:12]}{ext}"
    dest_path = settings.UPLOAD_DIR / safe_filename

    with open(dest_path, "wb") as f:
        f.write(contents)

    return {"photo_url": f"/static/uploads/{safe_filename}", "filename": safe_filename}

# Real application statistics endpoint (no fabricated live metrics)
@app.get("/api/stats", response_model=StatsOut)
def get_stats():
    total_reports = Database.fetch_one("SELECT COUNT(*) as c FROM reports")["c"]
    lost_count = Database.fetch_one("SELECT COUNT(*) as c FROM reports WHERE report_type = 'lost'")["c"]
    found_count = Database.fetch_one("SELECT COUNT(*) as c FROM reports WHERE report_type = 'found'")["c"]
    matched_count = Database.fetch_one("SELECT COUNT(*) as c FROM matches WHERE match_score >= 40")["c"]
    returned_count = Database.fetch_one("SELECT COUNT(*) as c FROM reports WHERE status = 'returned'")["c"]

    return StatsOut(
        total_reports=total_reports,
        lost_count=lost_count,
        found_count=found_count,
        matched_count=matched_count,
        returned_count=returned_count,
        campus=settings.COLLEGE_NAME
    )

# Demo data control endpoints
@app.post("/api/demo/seed")
def api_seed_demo():
    seed_demo_data()
    return {"status": "success", "message": "Demo data loaded successfully."}

@app.post("/api/demo/reset")
def api_reset_demo():
    reset_demo_data()
    return {"status": "success", "message": "Demo data reset successfully."}

# Single-Page Web Application entry point
@app.get("/", response_class=HTMLResponse)
def index_page():
    template_path = BASE_DIR / "app" / "templates" / "index.html"
    with open(template_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())
