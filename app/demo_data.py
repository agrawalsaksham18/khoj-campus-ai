import json
from datetime import datetime, timezone, timedelta
from app.database import Database
from app.matching_engine import sync_all_matches

DEMO_USERS = [
    {"id": "usr_aarav", "display_name": "Aarav Sharma (Y22 CSE)", "email": "aarav@iitk.ac.in"},
    {"id": "usr_priya", "display_name": "Priya Patel (Y21 EE)", "email": "priya@iitk.ac.in"},
    {"id": "usr_rohit", "display_name": "Rohit Verma (Y23 ME)", "email": "rohit@iitk.ac.in"},
    {"id": "usr_ananya", "display_name": "Ananya Singh (Y22 BSBE)", "email": "ananya@iitk.ac.in"}
]

def seed_demo_data():
    now = datetime.now(timezone.utc)
    t_yesterday = (now - timedelta(days=1)).isoformat()
    t_2days = (now - timedelta(days=2)).isoformat()
    t_today = now.isoformat()

    # 1. Insert Demo Users
    for u in DEMO_USERS:
        Database.execute("""
        INSERT OR IGNORE INTO users (id, display_name, email, created_at)
        VALUES (?, ?, ?, ?)
        """, (u["id"], u["display_name"], u["email"], t_2days))

    # 2. Insert Demo Reports
    demo_reports = [
        # Pair 1: Lost Black Milton Bottle
        {
            "id": "rep_demo_lost_bottle",
            "user_id": "usr_aarav",
            "report_type": "lost",
            "item_name": "Milton Black Water Bottle",
            "original_description": "Mera black Milton water bottle kal shaam ko PK Kelkar Library ke first floor reading room mein chhut gaya tha. Uspe ek round NASA space sticker laga hai.",
            "normalized_description": "Black Milton insulated water bottle with round NASA space sticker, lost at PK Kelkar Library reading room",
            "category": "bottles",
            "color": "Black",
            "brand": "Milton",
            "distinguishing_features": "Round NASA space sticker near lid, slight scratch at bottom",
            "location": "PK Kelkar Library",
            "occurrence_time": "Yesterday evening (approx 6:30 PM)",
            "photo_url": None,
            "preferred_language": "Hinglish",
            "status": "open",
            "is_demo": 1,
            "created_at": t_yesterday,
            "updated_at": t_yesterday
        },
        # Pair 1: Found Black Bottle
        {
            "id": "rep_demo_found_bottle",
            "user_id": "usr_priya",
            "report_type": "found",
            "item_name": "Black Insulated Water Bottle",
            "original_description": "Found a black Milton thermos bottle on the benches right outside PK Kelkar Central Library. Has a space agency sticker on it.",
            "normalized_description": "Black Milton thermos bottle with space sticker found on lawn outside PK Kelkar Library",
            "category": "bottles",
            "color": "Black",
            "brand": "Milton",
            "distinguishing_features": "Space theme circular sticker, metal cap",
            "location": "PK Kelkar Library",
            "occurrence_time": "Yesterday around 7:15 PM",
            "photo_url": None,
            "preferred_language": "English",
            "status": "open",
            "is_demo": 1,
            "created_at": t_yesterday,
            "updated_at": t_yesterday
        },

        # Pair 2: Lost Wildcraft Backpack
        {
            "id": "rep_demo_lost_bag",
            "user_id": "usr_rohit",
            "report_type": "lost",
            "item_name": "Navy Blue Wildcraft Backpack",
            "original_description": "Lost my navy blue Wildcraft backpack near SAC food court. It contains my EE200 circuit analysis notebook and a blue pencil pouch.",
            "normalized_description": "Navy blue Wildcraft backpack containing EE200 notebook and pencil pouch, lost at SAC food court",
            "category": "wallets_bags",
            "color": "Blue",
            "brand": "Wildcraft",
            "distinguishing_features": "White mountain logo, orange pull zippers, contains notebooks",
            "location": "Student Activity Centre (SAC)",
            "occurrence_time": "Two days ago afternoon",
            "photo_url": None,
            "preferred_language": "English",
            "status": "open",
            "is_demo": 1,
            "created_at": t_2days,
            "updated_at": t_2days
        },
        # Pair 2: Found Backpack
        {
            "id": "rep_demo_found_bag",
            "user_id": "usr_ananya",
            "report_type": "found",
            "item_name": "Blue Backpack (Wildcraft)",
            "original_description": "SAC food court ke concrete tables pe ek navy blue backpack mila. Safely deposited with SAC security desk.",
            "normalized_description": "Navy blue Wildcraft backpack found on tables at SAC food court, deposited with security",
            "category": "wallets_bags",
            "color": "Blue",
            "brand": "Wildcraft",
            "distinguishing_features": "Orange zipper tags, multiple compartments",
            "location": "Student Activity Centre (SAC)",
            "occurrence_time": "Two days ago evening",
            "photo_url": None,
            "preferred_language": "Hinglish",
            "status": "open",
            "is_demo": 1,
            "created_at": t_2days,
            "updated_at": t_2days
        },

        # Sensitive Item Example: Student ID Card (Demonstrates Privacy Masking)
        {
            "id": "rep_demo_lost_id",
            "user_id": "usr_aarav",
            "report_type": "lost",
            "item_name": "IITK Student Identity Card",
            "original_description": "Mera IIT Kanpur ID card gir gaya LHC L-7 ke paas. Name: Aarav Sharma, Roll No: 220145. Contact 9876543210 if found.",
            "normalized_description": "IITK Student ID Card for Aarav Sharma (Roll: 220145) lost near LHC L-7",
            "category": "id_cards",
            "color": "White",
            "brand": "IIT Kanpur",
            "distinguishing_features": "Y22 CSE batch card with blue lanyard and metallic clip",
            "location": "Lecture Hall Complex (LHC)",
            "occurrence_time": "Today morning 9:00 AM",
            "photo_url": None,
            "preferred_language": "Hinglish",
            "status": "open",
            "is_demo": 1,
            "created_at": t_today,
            "updated_at": t_today
        },

        # Non-matching item: Red notebook in Hall 3
        {
            "id": "rep_demo_found_notebook",
            "user_id": "usr_priya",
            "report_type": "found",
            "item_name": "Red Classmate Spiral Notebook",
            "original_description": "Found a red spiral notebook with handwritten MTH101 calculus notes in Hall 3 reading room.",
            "normalized_description": "Red Classmate spiral notebook with MTH101 notes found in Hall 3 reading room",
            "category": "books_stationery",
            "color": "Red",
            "brand": "Classmate",
            "distinguishing_features": "Name on first page torn out",
            "location": "Hall of Residence 3",
            "occurrence_time": "Yesterday night",
            "photo_url": None,
            "preferred_language": "English",
            "status": "open",
            "is_demo": 1,
            "created_at": t_yesterday,
            "updated_at": t_yesterday
        }
    ]

    for r in demo_reports:
        Database.execute("""
        INSERT OR REPLACE INTO reports (
            id, user_id, report_type, item_name, original_description,
            normalized_description, category, color, brand,
            distinguishing_features, location, occurrence_time,
            photo_url, preferred_language, status, is_demo,
            created_at, updated_at
        ) VALUES (
            :id, :user_id, :report_type, :item_name, :original_description,
            :normalized_description, :category, :color, :brand,
            :distinguishing_features, :location, :occurrence_time,
            :photo_url, :preferred_language, :status, :is_demo,
            :created_at, :updated_at
        )
        """, r)

    # Automatically compute matches for demo pairs
    sync_all_matches()

def reset_demo_data():
    Database.execute("DELETE FROM matches WHERE lost_report_id IN (SELECT id FROM reports WHERE is_demo = 1) OR found_report_id IN (SELECT id FROM reports WHERE is_demo = 1)")
    Database.execute("DELETE FROM reports WHERE is_demo = 1")
    seed_demo_data()
