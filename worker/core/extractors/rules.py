# core/extractors/rules.py
from __future__ import annotations
from typing import Any, Dict, List, Tuple
import re

PROMO_SENDER_HINTS = ("noreply", "no-reply", "newsletter", "marketing", "promo")
PROMO_TEXT_HINTS = ("unsubscribe", "sale", "discount", "limited time", "offer")

def _text(payload: Dict[str, Any]) -> str:
    subj = (payload.get("subject") or "")
    snip = (payload.get("snippet") or "")
    return f"{subj} {snip}".strip().lower()

def classify_promo(payload: Dict[str, Any]) -> bool:
    sender = (payload.get("from") or "").lower()
    t = _text(payload)
    if any(h in sender for h in PROMO_SENDER_HINTS):
        return True
    if any(h in t for h in PROMO_TEXT_HINTS):
        return True
    return False

def infer_intent(payload: Dict[str, Any]) -> str:
    t = _text(payload)
    # minimal intents to start
    if any(k in t for k in ("are you available", "availability", "schedule", "time works", "when can")):
        return "schedule"
    if any(k in t for k in ("confirm", "reply", "respond")):
        return "draft_reply"
    if any(k in t for k in ("remind", "follow up", "deadline", "due")):
        return "task"
    return "info"

def extract_action_items(payload: Dict[str, Any], intent: str) -> List[str]:
    t = _text(payload)
    actions: List[str] = []
    if intent == "schedule" and ("available" in t or "availability" in t):
        actions.append("Respond with availability")
    if "please let me know" in t:
        actions.append("Reply with requested information")
    return actions

def score_confidence(intent: str, is_promo: bool, actions: List[str]) -> float:
    # deterministic heuristic scoring (0..1)
    if is_promo:
        return 0.25
    base = 0.55
    if intent in ("schedule", "draft_reply", "task"):
        base += 0.15
    if actions:
        base += 0.15
    return min(base, 0.95)

def build_extraction_data(payload: Dict[str, Any]) -> Tuple[Dict[str, Any], float]:
    is_promo = classify_promo(payload)
    intent = infer_intent(payload)
    actions = extract_action_items(payload, intent)
    confidence = score_confidence(intent, is_promo, actions)

    data = {
        "intent": intent,
        "is_promo": is_promo,
        "action_items": actions,
        # optional metadata you can use later
        "sender": payload.get("from"),
        "thread_id": payload.get("thread_id"),
    }
    return data, confidence
