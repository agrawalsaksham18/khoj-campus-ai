import pytest
from app.database import init_db, Database
from app.schemas import ReportCreate, ReportUpdate, AIAnalyzeRequest
from app.api.reports import create_report, list_reports, get_report, update_report
from app.api.matches import list_matches, get_match, express_interest
from app.privacy import mask_sensitive_text, sanitize_report_for_public
from app.sarvam_service import SarvamService
from app.matching_engine import compute_match, find_matches_for_report, sync_all_matches

@pytest.fixture(autouse=True)
def setup_test_db():
    init_db()
    # Clean test state before test
    Database.execute("DELETE FROM matches")
    Database.execute("DELETE FROM reports")
    Database.execute("DELETE FROM users")
    
    # Create test user
    Database.execute("""
    INSERT OR REPLACE INTO users (id, display_name, email, created_at)
    VALUES ('usr_test', 'Test Student', 'test@iitk.ac.in', '2026-10-26T00:00:00')
    """)
    yield

# 1. Test Creating a Lost report
def test_create_lost_report():
    payload = ReportCreate(
        report_type="lost",
        item_name="Milton Steel Bottle",
        original_description="Mera black Milton bottle library me kho gaya tha kal shaam",
        category="bottles",
        color="Black",
        brand="Milton",
        location="PK Kelkar Library",
        user_id="usr_test"
    )
    result = create_report(payload)
    assert result["item_name"] == "Milton Steel Bottle"
    assert result["report_type"] == "lost"
    assert result["status"] == "open"
    assert result["id"].startswith("rep_")

    # Verify report is in database
    db_item = Database.fetch_one("SELECT * FROM reports WHERE id = ?", (result["id"],))
    assert db_item is not None
    assert db_item["category"] == "bottles"

# 2. Test Creating a Found report
def test_create_found_report():
    payload = ReportCreate(
        report_type="found",
        item_name="Found Steel Flask",
        original_description="Found a black insulated flask on the library grass lawn",
        category="bottles",
        color="Black",
        brand="Milton",
        location="PK Kelkar Library",
        user_id="usr_test"
    )
    result = create_report(payload)
    assert result["item_name"] == "Found Steel Flask"
    assert result["report_type"] == "found"
    assert result["status"] == "open"

# 3. Test Validating multilingual AI output
def test_multilingual_ai_output_hindi_hinglish():
    service = SarvamService()
    # Test Hinglish input
    hinglish_text = "Mera black wallet library ke bahar kal shaam kho gaya tha. Uske andar college ID thi."
    result = service.analyze_description(hinglish_text)
    
    assert result.item_type is not None
    assert result.category == "wallets_bags"
    assert result.color == "Black"
    assert "Library" in result.location
    assert result.language_detected in ["Hinglish", "Hindi", "multilingual"]

# 4. Test Handling missing or malformed AI responses
def test_handling_malformed_or_empty_ai_response():
    service = SarvamService()
    # Empty string input
    empty_result = service.analyze_description("")
    assert empty_result.is_ai_powered is False
    
    # Text with unknown / generic input
    gibberish_result = service.analyze_description("random text lost somewhere")
    assert gibberish_result.category == "others"
    assert gibberish_result.location is not None

# 5. Test Matching compatible reports
def test_matching_compatible_reports():
    lost_rep = {
        "id": "rep_lost_1",
        "report_type": "lost",
        "item_name": "Milton Black Bottle",
        "original_description": "Lost my black Milton bottle with NASA sticker near library",
        "normalized_description": "Black Milton water bottle with NASA space sticker",
        "category": "bottles",
        "color": "Black",
        "brand": "Milton",
        "distinguishing_features": "NASA space sticker",
        "location": "PK Kelkar Library",
        "occurrence_time": "Yesterday evening"
    }

    found_rep = {
        "id": "rep_found_1",
        "report_type": "found",
        "item_name": "Black Insulated Bottle",
        "original_description": "Found black bottle on lawn outside PK Kelkar library with space sticker",
        "normalized_description": "Black Milton water bottle with space sticker",
        "category": "bottles",
        "color": "Black",
        "brand": "Milton",
        "distinguishing_features": "Space sticker",
        "location": "PK Kelkar Library",
        "occurrence_time": "Yesterday evening"
    }

    score, reasons = compute_match(lost_rep, found_rep)
    assert score >= 70.0 # High match score
    assert any("Matching category" in r for r in reasons)
    assert any("Black" in r for r in reasons)
    assert any("Milton" in r for r in reasons)

# 6. Test Rejecting incompatible report types
def test_rejecting_incompatible_report_types():
    rep_lost_1 = {"id": "1", "report_type": "lost", "category": "bottles"}
    rep_lost_2 = {"id": "2", "report_type": "lost", "category": "bottles"}
    
    with pytest.raises(ValueError, match="Matching is only valid between a Lost report and a Found report"):
        compute_match(rep_lost_1, rep_lost_2)

# 7. Test Handling missing fields in matching
def test_matching_with_missing_fields():
    lost_minimal = {
        "id": "rep_l_min",
        "report_type": "lost",
        "item_name": "Keys",
        "original_description": "Lost bunch of keys",
        "category": "keys",
        "color": None,
        "brand": None,
        "distinguishing_features": None,
        "location": "Campus",
        "occurrence_time": None
    }
    
    found_minimal = {
        "id": "rep_f_min",
        "report_type": "found",
        "item_name": "Keys found",
        "original_description": "Found keys",
        "category": "keys",
        "color": None,
        "brand": None,
        "distinguishing_features": None,
        "location": "Campus",
        "occurrence_time": None
    }
    
    # Missing fields must not cause errors and must not be treated as a mismatch
    score, reasons = compute_match(lost_minimal, found_minimal)
    assert score > 0.0
    assert any("Matching category" in r for r in reasons)

# 8. Test Handling unavailable Sarvam API gracefully
def test_unavailable_sarvam_api_graceful_fallback():
    service = SarvamService()
    service._client = None # simulate offline / no API key
    
    res = service.analyze_description("Mera blue bag canteen me chhut gaya")
    assert res.category == "wallets_bags"
    assert res.color == "Blue"
    assert res.is_ai_powered is False
    assert "rule-based" in res.notes.lower()

# 9. Test Protecting sensitive data from public output
def test_protecting_sensitive_data_masking():
    # Test roll number masking
    raw_text = "Lost my ID card. Name: Rahul Sharma, Roll No: 210854, Phone: 9876543210. Email: rahul@iitk.ac.in."
    masked = mask_sensitive_text(raw_text)
    
    assert "210854" not in masked
    assert "9876543210" not in masked
    assert "rahul@iitk.ac.in" not in masked
    assert "••••" in masked

    # Test report sanitization
    sensitive_report = {
        "id": "rep_id_test",
        "category": "id_cards",
        "item_name": "Student ID Card",
        "original_description": "My roll no is 220145 and phone is 9876543210",
        "normalized_description": "Student ID card for 220145",
        "distinguishing_features": "ID card with roll 220145 and room 204"
    }
    sanitized = sanitize_report_for_public(sensitive_report)
    assert "220145" not in sanitized["original_description"]
    assert "9876543210" not in sanitized["original_description"]
    assert "220145" not in sanitized["distinguishing_features"]
