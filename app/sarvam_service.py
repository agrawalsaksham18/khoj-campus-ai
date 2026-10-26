import json
import logging
import re
import tempfile
from typing import Optional, Dict, Any, Tuple
from pathlib import Path

from app.config import settings
from app.schemas import AIAnalyzeResponse

logger = logging.getLogger("khoj.sarvam")

# Mapping of categories for normalisation
CATEGORY_KEYWORDS = {
    "bottles": ["bottle", "water bottle", "sipper", "flask", "milton", "thermos", "paani ki botal", "botal", "bootal"],
    "wallets_bags": ["wallet", "purse", "bag", "backpack", "pouch", "batua", "jhola", "wildcraft", "americantourister"],
    "id_cards": ["id", "id card", "identity card", "iitk id", "campus id", "hall pass", "card", "driving license", "pan card", "roll number"],
    "electronics": ["laptop", "earphones", "airpods", "headphones", "phone", "mobile", "charger", "powerbank", "ipad", "tablet", "calculator", "smartwatch", "watch", "casio"],
    "keys": ["key", "keys", "chabi", "chhabbi", "keychain", "bike key", "room key", "cycle key"],
    "books_stationery": ["notebook", "book", "register", "pen", "notes", "pencil", "geometry box", "file", "folder", "kitab"],
    "clothing": ["jacket", "hoodie", "sweater", "cap", "umbrella", "muffler", "chhatri", "gloves", "towel"],
    "accessories": ["glasses", "spectacles", "chashma", "ring", "chain", "bracelet", "belt"]
}

COLOR_KEYWORDS = {
    "black": ["black", "kala", "kaale", "kaali", "dark"],
    "blue": ["blue", "neela", "neeli", "navy blue", "cyan"],
    "red": ["red", "laal"],
    "white": ["white", "safed"],
    "silver": ["silver", "grey", "gray"],
    "green": ["green", "hara", "hari"],
    "yellow": ["yellow", "peela"],
    "brown": ["brown", "bhoora"],
    "pink": ["pink", "gulabi"],
    "orange": ["orange", "saffron", "narangi"]
}

LOCATION_KEYWORDS = {
    "PK Kelkar Library": ["library", "kelkar", "reading room", "reference section", "circulation desk"],
    "Lecture Hall Complex (LHC)": ["lhc", "l-7", "l-1", "l-16", "l-20", "lecture hall", "tutorial block"],
    "Student Activity Centre (SAC)": ["sac", "oat", "open air theatre", "canteen", "food court"],
    "Pronite Ground": ["pronite", "ground", "main ground", "antaragni ground"],
    "Computer Centre (CC)": ["cc", "computer centre", "lab"],
    "Health Centre (HC)": ["hc", "health centre", "hospital", "dispensary"],
    "Hall of Residence 1": ["hall 1", "hall-1", "h1"],
    "Hall of Residence 2": ["hall 2", "hall-2", "h2"],
    "Hall of Residence 3": ["hall 3", "hall-3", "h3"],
    "Hall of Residence 4": ["hall 4", "hall-4", "h4"],
    "Hall of Residence 12": ["hall 12", "hall-12", "h12"],
    "Hall of Residence 13": ["hall 13", "hall-13", "h13"],
    "CCD / DoAA Canteen": ["ccd", "cafe coffee day", "doaa", "faculty building", "fb"]
}

class SarvamService:
    def __init__(self):
        self._client = None
        self._init_client()

    def _init_client(self):
        if settings.has_sarvam_key:
            try:
                from sarvamai import SarvamAI
                self._client = SarvamAI(api_subscription_key=settings.SARVAM_API_KEY)
                logger.info("Sarvam AI SDK client initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Sarvam AI SDK: {e}")
                self._client = None
        else:
            self._client = None
            logger.info("No SARVAM_API_KEY detected. Running in heuristic fallback mode.")

    @property
    def is_available(self) -> bool:
        return self._client is not None

    def analyze_description(self, text: str, preferred_lang: Optional[str] = None) -> AIAnalyzeResponse:
        """
        Extracts structured attributes from multilingual report text (Hindi, Hinglish, English).
        Uses Sarvam's conversational chat completion model when API key is available.
        Falls back to rule-based parser if API key is absent or request fails.
        """
        if not text or not text.strip():
            return AIAnalyzeResponse(
                notes="Empty text provided",
                is_ai_powered=False
            )

        # Attempt Sarvam AI analysis if configured
        if self.is_available:
            try:
                return self._call_sarvam_chat_extraction(text, preferred_lang)
            except Exception as e:
                logger.warning(f"Sarvam AI chat call failed: {e}. Falling back to heuristic extractor.")
                fallback = self._heuristic_extraction(text)
                fallback.notes = f"Sarvam AI service encountered an error ({str(e)}). Heuristic parser applied."
                return fallback
        else:
            # Rule-based extraction
            res = self._heuristic_extraction(text)
            res.notes = "Offline rule-based parser (Configure SARVAM_API_KEY in .env for Sarvam 105B AI)."
            return res

    def _call_sarvam_chat_extraction(self, text: str, preferred_lang: Optional[str] = None) -> AIAnalyzeResponse:
        system_prompt = (
            "You are KHOJ, an AI assistant for IIT Kanpur's Lost & Found platform. "
            "Your task is to analyze user reports written in Hindi, English, or Hinglish, "
            "and extract structured attributes about the item. "
            "You MUST output valid JSON ONLY with these keys:\n"
            "{\n"
            '  "item_type": "short item name (e.g. Water Bottle, Wallet, ID Card)",\n'
            '  "category": "one of: [electronics, id_cards, wallets_bags, bottles, keys, books_stationery, clothing, accessories, others]",\n'
            '  "color": "primary color if stated, or null",\n'
            '  "brand": "brand or make if stated, or null",\n'
            '  "distinguishing_features": "stickers, scratches, contents, marks, or null",\n'
            '  "location": "campus location where lost/found, or null",\n'
            '  "approximate_time": "when lost/found (e.g. yesterday evening, 10am), or null",\n'
            '  "normalized_description": "concise, standardized English description of the item",\n'
            '  "language_detected": "Hindi, Hinglish, or English"\n'
            "}\n"
            "CRITICAL: Do NOT invent missing details. If an attribute is not mentioned in the text, return null."
        )

        user_content = f"User report text:\n'''{text}'''"
        if preferred_lang and preferred_lang != "unknown":
            user_content += f"\nUser indicated preferred language: {preferred_lang}"

        # Call Sarvam Chat completions using official SDK
        # We can use model 'sarvam-105b' or 'sarvam-105b-conversations'
        response = self._client.chat.completions(
            model="sarvam-105b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0.1
        )

        reply_content = response.choices[0].message.content.strip()
        # Clean potential markdown formatting like ```json ... ```
        if reply_content.startswith("```"):
            reply_content = re.sub(r"^```(?:json)?\n?", "", reply_content)
            reply_content = re.sub(r"\n?```$", "", reply_content)

        data = json.loads(reply_content)

        # Validate category against valid set
        valid_categories = {"electronics", "id_cards", "wallets_bags", "bottles", "keys", "books_stationery", "clothing", "accessories", "others"}
        raw_cat = (data.get("category") or "others").lower().replace(" ", "_")
        category = raw_cat if raw_cat in valid_categories else "others"

        return AIAnalyzeResponse(
            item_type=data.get("item_type"),
            category=category,
            color=data.get("color"),
            brand=data.get("brand"),
            distinguishing_features=data.get("distinguishing_features"),
            location=data.get("location"),
            approximate_time=data.get("approximate_time"),
            normalized_description=data.get("normalized_description") or text[:120],
            language_detected=data.get("language_detected", "multilingual"),
            is_ai_powered=True,
            notes="Processed via Sarvam 105B Conversational Model"
        )

    def _heuristic_extraction(self, text: str) -> AIAnalyzeResponse:
        """
        Robust heuristic extraction for Hindi, Hinglish, and English text
        when offline or before API key is configured.
        """
        text_lower = text.lower()

        # Detect category
        matched_category = "others"
        item_type = "Belonging"
        for cat, keywords in CATEGORY_KEYWORDS.items():
            for kw in keywords:
                if kw in text_lower:
                    matched_category = cat
                    item_type = kw.title()
                    break
            if matched_category != "others":
                break

        # Detect color
        matched_color = None
        for color, keywords in COLOR_KEYWORDS.items():
            for kw in keywords:
                if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
                    matched_color = color.title()
                    break
            if matched_color:
                break

        # Detect brand
        matched_brand = None
        brands = ["milton", "tupperware", "wildcraft", "nike", "adidas", "apple", "hp", "dell", "lenovo", "casio", "boat", "sony", "titan", "fastrack", "caterpillar"]
        for b in brands:
            if b in text_lower:
                matched_brand = b.title()
                break

        # Detect location
        matched_location = None
        for loc, keywords in LOCATION_KEYWORDS.items():
            for kw in keywords:
                if kw in text_lower:
                    matched_location = loc
                    break
            if matched_location:
                break
        if not matched_location:
            matched_location = "IIT Kanpur Campus"

        # Detect time
        matched_time = None
        time_terms = {
            "Yesterday evening": ["kal shaam", "kal sham", "yesterday evening"],
            "Yesterday": ["kal", "yesterday"],
            "Today morning": ["aaj subah", "today morning"],
            "Today": ["aaj", "today"],
            "Last night": ["kal raat", "last night"]
        }
        for label, terms in time_terms.items():
            for term in terms:
                if term in text_lower:
                    matched_time = label
                    break
            if matched_time:
                break

        # Distinguishing features
        dist_features = None
        if "sticker" in text_lower:
            dist_features = "Has sticker"
        elif "id" in text_lower and matched_category == "wallets_bags":
            dist_features = "Contains ID card"
        elif "keychain" in text_lower:
            dist_features = "Attached keychain"

        # Language detection heuristic
        has_devanagari = any('\u0900' <= char <= '\u097F' for char in text)
        hinglish_markers = ["mera", "meri", "chhut", "gaya", "gayi", "kho", "mila", "mili", "paani", "andar", "bahar", "bhai", "kripya"]
        has_hinglish = any(m in text_lower for m in hinglish_markers)

        if has_devanagari:
            lang = "Hindi"
        elif has_hinglish:
            lang = "Hinglish"
        else:
            lang = "English"

        # Formulate normalized description
        parts = []
        if matched_color:
            parts.append(matched_color)
        if matched_brand:
            parts.append(matched_brand)
        parts.append(item_type)
        if matched_location:
            parts.append(f"reported at {matched_location}")
        normalized = " ".join(parts) if parts else text[:100]

        return AIAnalyzeResponse(
            item_type=item_type,
            category=matched_category,
            color=matched_color,
            brand=matched_brand,
            distinguishing_features=dist_features,
            location=matched_location,
            approximate_time=matched_time,
            normalized_description=normalized,
            language_detected=lang,
            is_ai_powered=False,
            notes="Extracted using offline rule-based parser"
        )

    def transcribe_audio(self, audio_bytes: bytes, filename: str, mime_type: str = "audio/webm") -> Tuple[str, str]:
        """
        Transcribes speech using Sarvam Speech-to-Text (Saaras model).
        Returns: (transcript_text, detected_language)
        """
        if not self.is_available:
            raise RuntimeError(
                "Sarvam AI API key is not configured. "
                "Please add SARVAM_API_KEY in .env to use Sarvam Voice Speech-to-Text."
            )

        suffix = Path(filename).suffix or ".webm"
        # Determine codec
        codec = "webm"
        if suffix in [".wav", ".wave"]:
            codec = "wav"
        elif suffix in [".mp3"]:
            codec = "mp3"
        elif suffix in [".ogg", ".opus"]:
            codec = "ogg"

        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            with open(tmp_path, "rb") as audio_file:
                # Use Saaras:v4 as recommended in docs
                response = self._client.speech_to_text.transcribe(
                    file=audio_file,
                    model="saaras:v4",
                    mode="codemix",
                    language_code="unknown",
                    input_audio_codec=codec
                )
            transcript = getattr(response, "transcript", "")
            detected_lang = getattr(response, "language_code", "hi-IN")
            return transcript, detected_lang
        finally:
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except Exception:
                pass

sarvam_service = SarvamService()
