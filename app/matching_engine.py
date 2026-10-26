import re
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple, Optional
from app.database import Database

# Configurable matching weights (as requested in Section 3)
MATCH_WEIGHTS = {
    "category": 0.30,        # Item type / category (30%)
    "features": 0.25,        # Distinguishing features & description (25%)
    "color_brand": 0.15,     # Colour & brand (15%)
    "location": 0.15,        # Location proximity (15%)
    "time": 0.15             # Time proximity (15%)
}

# Campus location proximity clusters for IIT Kanpur
LOCATION_CLUSTERS = {
    "library_academic": [
        "pk kelkar library", "library", "central library", "reading room",
        "lecture hall complex", "lhc", "tutorial block",
        "computer centre", "cc", "faculty building", "fb", "doaa", "ccd"
    ],
    "sac_central": [
        "student activity centre", "sac", "oat", "open air theatre",
        "health centre", "hc", "sac food court", "canteen"
    ],
    "grounds_sports": [
        "pronite ground", "main ground", "antaragni ground", "football ground",
        "gymkhana", "swimming pool"
    ],
    "hostels_north": [
        "hall of residence 1", "hall 1", "hall of residence 2", "hall 2",
        "hall of residence 3", "hall 3", "hall of residence 5", "hall 5"
    ],
    "hostels_west": [
        "hall of residence 12", "hall 12", "hall of residence 13", "hall 13",
        "hall of residence 14", "hall 14"
    ]
}

def tokenize(text: Optional[str]) -> set:
    if not text:
        return set()
    # remove punctuation and lowercase
    cleaned = re.sub(r'[^\w\s]', ' ', text.lower())
    words = cleaned.split()
    # filter short noise words
    stop_words = {"the", "a", "an", "is", "in", "at", "of", "on", "and", "or", "to", "my", "mera", "meri", "tha", "thi", "hai", "ko"}
    return {w for w in words if len(w) > 2 and w not in stop_words}

def compute_text_similarity(text1: Optional[str], text2: Optional[str]) -> float:
    t1 = tokenize(text1)
    t2 = tokenize(text2)
    if not t1 or not t2:
        return 0.5 # Neutral if one or both missing
    intersection = t1.intersection(t2)
    union = t1.union(t2)
    return len(intersection) / len(union)

def compute_location_proximity(loc1: Optional[str], loc2: Optional[str]) -> Tuple[float, Optional[str]]:
    if not loc1 or not loc2:
        return 0.5, None # Neutral if missing
    
    l1, l2 = loc1.strip().lower(), loc2.strip().lower()
    if l1 == l2 or l1 in l2 or l2 in l1:
        return 1.0, f"Identical location reported: '{loc1}'"
    
    # Check cluster proximity
    for cluster_name, loc_list in LOCATION_CLUSTERS.items():
        in_1 = any(alias in l1 for alias in loc_list)
        in_2 = any(alias in l2 for alias in loc_list)
        if in_1 and in_2:
            return 0.75, f"Nearby locations within same campus area ('{loc1}' and '{loc2}')"
            
    return 0.2, None

def compute_match(lost_rep: Dict[str, Any], found_rep: Dict[str, Any]) -> Tuple[float, List[str]]:
    """
    Computes an explainable match score between a Lost report and a Found report.
    Returns: (score between 0 and 100, list of reasons)
    """
    # Safety rule: Only compare compatible Lost vs Found reports
    if lost_rep.get("report_type") != "lost" or found_rep.get("report_type") != "found":
        raise ValueError("Matching is only valid between a Lost report and a Found report.")

    reasons = []
    total_score = 0.0

    # 1. Category & Item Type (30%)
    cat_lost = (lost_rep.get("category") or "").lower()
    cat_found = (found_rep.get("category") or "").lower()
    
    if cat_lost and cat_found and cat_lost == cat_found:
        cat_score = 1.0
        reasons.append(f"Matching category: both are '{cat_lost.replace('_', ' ').title()}'")
    else:
        # Check title overlap
        title_sim = compute_text_similarity(lost_rep.get("item_name"), found_rep.get("item_name"))
        if title_sim >= 0.5:
            cat_score = 0.8
            reasons.append("Item names share similar descriptors")
        elif not cat_lost or not cat_found:
            cat_score = 0.5 # Neutral if unclassified
        else:
            cat_score = 0.0
    total_score += cat_score * MATCH_WEIGHTS["category"]

    # 2. Distinguishing Features & Normalized Description (25%)
    feat_lost = lost_rep.get("distinguishing_features") or lost_rep.get("normalized_description") or lost_rep.get("original_description")
    feat_found = found_rep.get("distinguishing_features") or found_rep.get("normalized_description") or found_rep.get("original_description")
    
    feat_sim = compute_text_similarity(feat_lost, feat_found)
    # Check specific keyword overlap (e.g. stickers, case, brand)
    t_lost = tokenize(feat_lost)
    t_found = tokenize(feat_found)
    shared_tokens = t_lost.intersection(t_found)
    
    if shared_tokens:
        reasons.append(f"Shared descriptive keywords: {', '.join(list(shared_tokens)[:4])}")
        feat_score = min(1.0, 0.4 + (len(shared_tokens) * 0.2))
    else:
        feat_score = feat_sim
    total_score += feat_score * MATCH_WEIGHTS["features"]

    # 3. Colour & Brand (15%)
    color_lost = (lost_rep.get("color") or "").lower().strip()
    color_found = (found_rep.get("color") or "").lower().strip()
    brand_lost = (lost_rep.get("brand") or "").lower().strip()
    brand_found = (found_rep.get("brand") or "").lower().strip()

    color_score = 0.5
    if color_lost and color_found:
        if color_lost == color_found:
            color_score = 1.0
            reasons.append(f"Matching colour: '{color_lost.title()}'")
        else:
            color_score = 0.0
    
    brand_score = 0.5
    if brand_lost and brand_found:
        if brand_lost == brand_found:
            brand_score = 1.0
            reasons.append(f"Matching brand: '{brand_lost.title()}'")
        else:
            brand_score = 0.0

    cb_score = (color_score + brand_score) / 2.0
    total_score += cb_score * MATCH_WEIGHTS["color_brand"]

    # 4. Location Proximity (15%)
    loc_score, loc_reason = compute_location_proximity(lost_rep.get("location"), found_rep.get("location"))
    if loc_reason:
        reasons.append(loc_reason)
    total_score += loc_score * MATCH_WEIGHTS["location"]

    # 5. Time Proximity (15%)
    # If both indicate occurrence time, compare overlap
    time_lost = (lost_rep.get("occurrence_time") or "").lower().strip()
    time_found = (found_rep.get("occurrence_time") or "").lower().strip()
    time_score = 0.5
    if time_lost and time_found:
        time_sim = compute_text_similarity(time_lost, time_found)
        if time_sim >= 0.4 or time_lost in time_found or time_found in time_lost:
            time_score = 0.9
            reasons.append("Occurred around a similar timeframe")
        else:
            time_score = 0.3
    total_score += time_score * MATCH_WEIGHTS["time"]

    # Final score out of 100
    final_percentage = round(total_score * 100, 1)
    if not reasons:
        reasons.append("General item characteristics evaluated")

    return final_percentage, reasons

def find_matches_for_report(report_id: str, threshold: float = 35.0) -> List[Dict[str, Any]]:
    """
    Finds and ranks candidate matches for a given report (lost or found).
    """
    target = Database.fetch_one("SELECT * FROM reports WHERE id = ?", (report_id,))
    if not target:
        return []

    target_type = target["report_type"]
    opposite_type = "found" if target_type == "lost" else "lost"

    # Fetch candidate items of the opposite type that are active (open or matched)
    candidates = Database.fetch_all(
        "SELECT * FROM reports WHERE report_type = ? AND status IN ('open', 'matched') AND id != ?",
        (opposite_type, report_id)
    )

    matches = []
    for cand in candidates:
        lost_rep = target if target_type == "lost" else cand
        found_rep = cand if target_type == "lost" else target

        try:
            score, reasons = compute_match(lost_rep, found_rep)
            if score >= threshold:
                matches.append({
                    "lost_report_id": lost_rep["id"],
                    "found_report_id": found_rep["id"],
                    "target_report": target,
                    "matched_report": cand,
                    "match_score": score,
                    "matching_reasons": reasons
                })
        except ValueError:
            continue

    # Sort descending by match score
    matches.sort(key=lambda x: x["match_score"], reverse=True)
    return matches

def sync_all_matches():
    """
    Scans active reports and populates or updates the matches table in DB.
    """
    lost_reports = Database.fetch_all("SELECT * FROM reports WHERE report_type = 'lost' AND status IN ('open', 'matched')")
    found_reports = Database.fetch_all("SELECT * FROM reports WHERE report_type = 'found' AND status IN ('open', 'matched')")

    for l in lost_reports:
        for f in found_reports:
            score, reasons = compute_match(l, f)
            if score >= 35.0:
                match_id = f"match_{l['id']}_{f['id']}"
                now = datetime.now(timezone.utc).isoformat()
                Database.execute("""
                INSERT INTO matches (id, lost_report_id, found_report_id, match_score, matching_reasons, review_status, created_at)
                VALUES (?, ?, ?, ?, ?, 'pending', ?)
                ON CONFLICT(lost_report_id, found_report_id) DO UPDATE SET
                    match_score = excluded.match_score,
                    matching_reasons = excluded.matching_reasons
                """, (match_id, l["id"], f["id"], score, json.dumps(reasons), now))
