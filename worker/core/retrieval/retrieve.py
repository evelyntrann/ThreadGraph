# core/retrieval/retrieve.py
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import List, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import and_

from models import RawEvent, Extraction
from core.policy.policy import Policy

METHOD = "rule"

def retrieve_candidates(db: Session, policy: Policy) -> List[Tuple[RawEvent, Extraction]]:
    now = datetime.now(tz=timezone.utc)
    cutoff = now - timedelta(days=policy.max_days)

    q = (
        db.query(RawEvent, Extraction)
        .join(Extraction, and_(Extraction.event_id == RawEvent.id, Extraction.method == METHOD))
        .filter(RawEvent.occurred_at >= cutoff)
        .filter(Extraction.confidence >= policy.min_confidence)
        .order_by(RawEvent.occurred_at.desc())
        .limit(policy.max_items)
    )

    rows: List[Tuple[RawEvent, Extraction]] = q.all()
    if not policy.allow_promo:
        rows = [(e, x) for (e, x) in rows if not x.data.get("is_promo", False)]
    return rows
