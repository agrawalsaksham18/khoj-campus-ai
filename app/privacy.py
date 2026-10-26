import re
from typing import Optional

# Regex patterns for sensitive student data
PHONE_REGEX = re.compile(r'(?:\+?91[\-\s]?)?[6-9]\d{9}')
ROLL_NO_REGEX = re.compile(r'\b(?:\d{6,8}|Y\d{2}[A-Z]{2,4}\d{2,4}|2[0-9]{5,7})\b', re.IGNORECASE)
ID_CARD_REGEX = re.compile(r'\b(?:IITK[\-\/\s]?[A-Z0-9]{4,10}|ID[:\s]+[A-Z0-9]{4,12})\b', re.IGNORECASE)
EMAIL_REGEX = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
SERIAL_REGEX = re.compile(r'\b(?:S\/N|Serial|IMEI)[:\s]*([A-Za-z0-9\-]{6,20})\b', re.IGNORECASE)

def mask_phone_number(match: re.Match) -> str:
    val = match.group(0)
    digits = re.sub(r'\D', '', val)
    if len(digits) >= 10:
        return f"{digits[:2]}••••••{digits[-2:]}"
    return "••••••••••"

def mask_roll_number(match: re.Match) -> str:
    val = match.group(0)
    if len(val) <= 4:
        return "••••"
    return f"••{val[-3:]}"

def mask_email(match: re.Match) -> str:
    val = match.group(0)
    parts = val.split('@')
    name = parts[0]
    domain = parts[1] if len(parts) > 1 else "iitk.ac.in"
    masked_name = name[0] + "•••" if len(name) > 1 else "•"
    return f"{masked_name}@{domain}"

def mask_sensitive_text(text: Optional[str]) -> str:
    """
    Masks sensitive attributes like phone numbers, student roll numbers,
    ID card identifiers, serial numbers, and emails from public view.
    """
    if not text:
        return ""
    
    result = text
    # Mask emails
    result = EMAIL_REGEX.sub(mask_email, result)
    # Mask phone numbers
    result = PHONE_REGEX.sub(mask_phone_number, result)
    # Mask ID / serial tags
    result = ID_CARD_REGEX.sub(lambda m: f"IITK-ID-••••{m.group(0)[-2:] if len(m.group(0)) > 2 else ''}", result)
    # Mask roll numbers
    result = ROLL_NO_REGEX.sub(mask_roll_number, result)
    # Mask serial numbers / IMEI
    result = SERIAL_REGEX.sub("Serial: ••••••••", result)
    
    return result

def sanitize_report_for_public(report_dict: dict) -> dict:
    """
    Creates a copy of a report with sensitive fields masked for public browsing.
    """
    safe = dict(report_dict)
    
    # Check if category is sensitive (ID card, wallet, electronics)
    is_sensitive_cat = safe.get("category") in ("id_cards", "wallets_bags", "electronics")
    
    # Mask descriptions
    safe["original_description"] = mask_sensitive_text(safe.get("original_description", ""))
    safe["normalized_description"] = mask_sensitive_text(safe.get("normalized_description", ""))
    
    # If it's an ID card or wallet, mask distinguishing features for the public feed
    # Claimants verify details directly during the verification step
    dist_features = safe.get("distinguishing_features") or ""
    if is_sensitive_cat and dist_features:
        safe["distinguishing_features"] = mask_sensitive_text(dist_features)
    
    return safe
