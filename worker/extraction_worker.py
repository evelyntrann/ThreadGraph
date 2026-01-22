# worker/extraction_worker.py
from __future__ import annotations
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from db import SessionLocal
from models import RawEvent, Extraction
from core.extractors.rules import build_extraction_data

METHOD = "rule"

def upsert_extraction(db: Session, event: RawEvent) -> None:
    data, confidence = build_extraction_data(event.payload)

    base_stmt = insert(Extraction).values(
        event_id=event.id,
        method=METHOD,
        extracted_at=datetime.now(tz=timezone.utc),
        confidence=confidence,
        data=data,
    )

    # IMPORTANT: do not reference stmt before it exists
    stmt = base_stmt.on_conflict_do_update(
        constraint="uq_event_method",
        set_={
            "extracted_at": base_stmt.excluded.extracted_at,
            "confidence": base_stmt.excluded.confidence,
            "data": base_stmt.excluded.data,
        },
    )
    db.execute(stmt)

def run(batch_size: int = 200, only_missing: bool = True) -> int:
    db = SessionLocal()
    try:
        q = db.query(RawEvent)

        if only_missing:
            # Left join to find events without an extraction row
            q = (
                q.outerjoin(
                    Extraction,
                    (Extraction.event_id == RawEvent.id) & (Extraction.method == METHOD),
                )
                .filter(Extraction.id.is_(None))
            )

        events: List[RawEvent] = q.order_by(RawEvent.occurred_at.desc()).limit(batch_size).all()

        for e in events:
            upsert_extraction(db, e)

        db.commit()
        return len(events)
    finally:
        db.close()

if __name__ == "__main__":
    n = run(batch_size=500, only_missing=True)
    print(f"✅ Extraction worker processed {n} raw_event rows")
