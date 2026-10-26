# KHOJ (खोज) — Multilingual AI Lost & Found Platform

> **"Lost something on campus? Let's find it."**

Khoj is a modern, student-centric, AI-powered Lost & Found web platform initially designed for **IIT Kanpur**. It allows students to report lost or found belongings in **Hindi, English, or Hinglish** (via text or voice), automatically extracts structured attributes using **Sarvam AI**, and intelligently identifies and ranks potential matches through an explainable matching engine.

---

## 🌟 Key Features

1. **Multilingual Report Understanding**:
   - Accepts descriptions in Hindi (`"Mera black wallet library ke bahar chhut gaya"`), Hinglish, or English.
   - Extracts: item type, category, colour, brand, distinguishing features, location, and timeframe.
   - Powered by Sarvam's conversational chat model (`sarvam-105b` / `sarvam-105b-conversations`), with an intelligent offline heuristic parser fallback when no API key is set.

2. **Voice Reporting (Sarvam Saaras STT)**:
   - In-browser microphone recording with live audio timer and audio preview.
   - Transcribes speech across 22+ Indian languages and Hinglish using Sarvam's `saaras:v4` Speech-to-Text model (`mode="codemix"`).
   - Allows users to review and edit the transcript before submitting.

3. **Intelligent Explainable Matching Engine**:
   - Compares complementary Lost and Found reports with configurable weighted scoring:
     - **Item Type / Category**: 30%
     - **Distinguishing Features & Description**: 25%
     - **Colour & Brand**: 15%
     - **Campus Location Proximity** (IITK clusters: Library, LHC, SAC, CC, Hostels): 15%
     - **Time Proximity**: 15%
   - Missing fields are never penalized as mismatches.
   - Transparently displays exact matching reasons (e.g. *"Both items specify Milton black bottle"*, *"Reported at nearby locations (PK Kelkar Library)"*).

4. **Privacy & Trust Protections**:
   - Student ID numbers, roll numbers (e.g. `210854` → `••854`), phone numbers, and serial numbers are automatically masked from public feeds.
   - Safe verification claim workflow: claimants must supply specific proof of ownership details to the finder before collection.
   - Items are never automatically marked as returned by AI.

5. **Demo Experience**:
   - Built-in sample cases from IIT Kanpur (Lost Milton black bottle vs. Found black bottle at PK Kelkar Library, Wildcraft backpack at SAC, Student ID card, and an unrelated notebook).
   - One-click **Load Demo Data** and **Reset Demo Data** buttons for instant demonstration.

---

## 📁 Project Structure

```
khoj/
├── .env                  # Environment secrets (SARVAM_API_KEY) - gitignored
├── .env.example          # Template for environment configuration
├── .gitignore            # Git ignore rules protecting keys and database
├── pytest.ini            # Pytest configuration
├── requirements.txt      # Minimum dependencies
├── README.md             # Documentation and usage guide
├── khoj.db               # SQLite local database (created automatically)
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI server, endpoints, and static mount
│   ├── config.py         # Settings & environment variables
│   ├── database.py       # Thread-safe SQLite persistence layer
│   ├── models.py         # Domain models
│   ├── schemas.py        # Pydantic validation schemas
│   ├── privacy.py        # Privacy filters & sensitive data masking (Roll No, ID, Phone)
│   ├── sarvam_service.py # Official Sarvam AI SDK integration + heuristic fallback
│   ├── matching_engine.py# Explainable weighted matching engine & location clustering
│   ├── demo_data.py      # IIT Kanpur demonstration seed records
│   ├── api/
│   │   ├── __init__.py
│   │   ├── reports.py    # Report CRUD, filtering, and search endpoints
│   │   ├── matches.py    # Matches listing and verification claim routes
│   │   ├── ai.py         # AI extraction & status endpoints
│   │   └── voice.py      # Voice transcription endpoint (Sarvam STT)
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css # Warm campus theme & animations
│   │   ├── js/
│   │   │   └── app.js    # SPA state management, voice recording & UI logic
│   │   └── uploads/      # Safe local image uploads storage
│   └── templates/
│       └── index.html    # Responsive web interface with Tailwind CSS & Lucide icons
└── tests/
    ├── __init__.py
    └── test_khoj.py      # Comprehensive 9-part automated test suite
```

---

## 🚀 Quick Setup Instructions

### Prerequisites
- Python 3.10+ (Tested on Python 3.14)
- Pip

### 1. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 2. Configure Your Sarvam AI Key
Open the `.env` file in the project root:
```ini
SARVAM_API_KEY=your_actual_sarvam_api_key_here
```
> **Note**: The application is built with a graceful offline heuristic engine. If `SARVAM_API_KEY` is blank or not yet provided, the app continues to function smoothly in offline rule-based mode, clearly flagging that cloud AI is ready to be enabled once the key is pasted.

### 3. Run the Application
Start the FastAPI server:
```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open your web browser and navigate to:
```
http://127.0.0.1:8000
```

---

## 🧪 Running the Automated Test Suite

Khoj includes automated tests verifying all core requirements:
- Creating Lost reports
- Creating Found reports
- Validating multilingual AI output (Hindi & Hinglish)
- Handling missing or malformed AI responses
- Matching compatible reports
- Rejecting incompatible report types
- Handling missing fields in matching
- Handling unavailable Sarvam API gracefully
- Protecting sensitive data from public output (Roll numbers, IDs, Phones)

Run the test suite with:
```powershell
python -m pytest tests -v
```

All 9 tests pass out-of-the-box.

---

## 🔍 How to Test the Demo Experience

1. Launch the app and visit `http://127.0.0.1:8000`.
2. Look at the **Real Campus Stats** in the hero section.
3. Click **"AI Matches"** in the top navigation:
   - Notice the high-probability match (~90%) between **Aarav's Lost Milton Black Bottle** and **Priya's Found Black Insulated Bottle** at PK Kelkar Library.
   - Click **"Compare & Verify Details"** to view the attribute comparison and explainable matching reasons.
   - Test the **Safe Verification Claim** workflow by submitting proof notes.
4. Click **"Browse Reports"**:
   - Filter by category (e.g. *Water Bottles*, *Student IDs*, *Wallets & Bags*).
   - Search for `"library"` or `"sac"`.
   - Notice that the Student ID Card report masks the sensitive Roll Number (`••••145`) and phone number (`••••••••••`) from the public feed.
5. Click **"Report Item"**:
   - Type `"Mera black laptop bag LHC L-1 me chhut gaya tha"` and click **"AI Auto-Fill"** to watch the fields populate automatically!
   - If a microphone is available and `SARVAM_API_KEY` is configured, test the **Voice Recording** feature.
6. Use the **Load Demo Data** and **Reset Demo Data** buttons in the footer to restore or reset clean sample data at any time.

---

## 📋 Feature Status Matrix

| Feature | Status | Notes |
| :--- | :--- | :--- |
| **Multilingual Report Extraction** | **Working** | Powered by `sarvam-105b` when `SARVAM_API_KEY` is provided; uses offline Hindi/Hinglish NLP parser when offline. |
| **Voice Speech-to-Text** | **Working** | Integrated with `client.speech_to_text.transcribe` (`saaras:v4`, `mode="codemix"`). Requires valid `SARVAM_API_KEY` in `.env`. |
| **Explainable Matching Engine** | **Working** | Fully active with weighted algorithm (30/25/15/15/15%) and IITK location clustering. |
| **Privacy Masking** | **Working** | Masks Roll numbers, Student IDs, Phone numbers, and Emails from public view. |
| **Data Persistence** | **Working** | SQLite local database with auto-initialization and demo seed. |
| **Responsive UI & Mobile Web** | **Working** | Modern Tailwind CSS interface with warm campus palette and Lucide icons. |
| **Automated Tests** | **Working** | 9 passing unit and integration tests. |
