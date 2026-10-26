import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any
from app.config import BASE_DIR

DB_PATH = BASE_DIR / "khoj.db"

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_connection()
    with conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            display_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS reports (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            report_type TEXT NOT NULL CHECK(report_type IN ('lost', 'found')),
            item_name TEXT NOT NULL,
            original_description TEXT NOT NULL,
            normalized_description TEXT,
            category TEXT NOT NULL,
            color TEXT,
            brand TEXT,
            distinguishing_features TEXT,
            location TEXT NOT NULL,
            occurrence_time TEXT,
            photo_url TEXT,
            preferred_language TEXT DEFAULT 'en',
            status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open', 'matched', 'returned', 'closed')),
            is_demo INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_reports_type ON reports(report_type);
        CREATE INDEX IF NOT EXISTS idx_reports_category ON reports(category);
        CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status);
        CREATE INDEX IF NOT EXISTS idx_reports_user ON reports(user_id);
        CREATE INDEX IF NOT EXISTS idx_reports_created ON reports(created_at);

        CREATE TABLE IF NOT EXISTS matches (
            id TEXT PRIMARY KEY,
            lost_report_id TEXT NOT NULL,
            found_report_id TEXT NOT NULL,
            match_score REAL NOT NULL,
            matching_reasons TEXT NOT NULL,
            review_status TEXT NOT NULL DEFAULT 'pending' CHECK(review_status IN ('pending', 'interested', 'verified', 'rejected')),
            claimant_notes TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (lost_report_id) REFERENCES reports (id) ON DELETE CASCADE,
            FOREIGN KEY (found_report_id) REFERENCES reports (id) ON DELETE CASCADE,
            UNIQUE(lost_report_id, found_report_id)
        );

        CREATE INDEX IF NOT EXISTS idx_matches_lost ON matches(lost_report_id);
        CREATE INDEX IF NOT EXISTS idx_matches_found ON matches(found_report_id);
        CREATE INDEX IF NOT EXISTS idx_matches_score ON matches(match_score);
        """)

# Helper database operations
class Database:
    @staticmethod
    def execute(query: str, params: tuple = ()) -> sqlite3.Cursor:
        conn = get_connection()
        with conn:
            return conn.execute(query, params)

    @staticmethod
    def fetch_one(query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(query, params)
        row = cur.fetchone()
        return dict(row) if row else None

    @staticmethod
    def fetch_all(query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def commit_transaction(queries: List[tuple]):
        conn = get_connection()
        with conn:
            for q, p in queries:
                conn.execute(q, p)
