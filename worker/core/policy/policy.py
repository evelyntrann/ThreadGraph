# core/policy/policy.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional

@dataclass(frozen=True)
class Policy:
    max_days: int
    min_confidence: float
    allow_promo: bool = False
    max_items: int = 20

def infer_query_intent(query: str) -> str:
    q = query.lower()
    if any(k in q for k in ("draft", "reply", "email back", "respond")):
        return "draft_reply"
    if any(k in q for k in ("schedule", "available", "availability", "meeting")):
        return "schedule"
    if any(k in q for k in ("todo", "task", "deadline", "due")):
        return "task"
    return "info"

def policy_for_intent(intent: str) -> Policy:
    # start strict; relax later
    if intent == "draft_reply":
        return Policy(max_days=14, min_confidence=0.55, allow_promo=False, max_items=20)
    if intent == "schedule":
        return Policy(max_days=30, min_confidence=0.55, allow_promo=False, max_items=25)
    if intent == "task":
        return Policy(max_days=45, min_confidence=0.55, allow_promo=False, max_items=25)
    return Policy(max_days=30, min_confidence=0.6, allow_promo=False, max_items=15)
