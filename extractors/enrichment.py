# enrichment.py
from datetime import datetime, timezone
from models import Extraction
from extractors.rules import extract_intent, is_promotional, extract_action_items

def build_extraction(raw_event):
    intent = extract_intent(raw_event.payload)
    promo = is_promotional(raw_event.payload)
    actions = extract_action_items(raw_event.payload)

    data = {
        "intent": intent,
        "is_promo": promo,
        "action_items": actions,
    }

    confidence = 0.7 if not promo else 0.4

    return {
        "method": "rule",
        "extracted_at": datetime.now(tz=timezone.utc),
        "confidence": confidence,
        "data": data,
    }
