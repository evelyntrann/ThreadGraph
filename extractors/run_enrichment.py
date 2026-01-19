# run_enrichment.py
from sqlalchemy.dialects.postgresql import insert
from db import SessionLocal
from models import RawEvent, Extraction
from enrichment import build_extraction

def run():
    db = SessionLocal()

    events = db.query(RawEvent).all()

    for event in events:
        extraction = build_extraction(event)

        stmt = insert(Extraction).values(
            event_id=event.id,
            method=extraction["method"],
            extracted_at=extraction["extracted_at"],
            confidence=extraction["confidence"],
            data=extraction["data"],
        ).on_conflict_do_update(
            constraint="uq_event_method",
            set_={
                "extracted_at": stmt.excluded.extracted_at,
                "confidence": stmt.excluded.confidence,
                "data": stmt.excluded.data,
            }
        )

        db.execute(stmt)

    db.commit()
    db.close()

if __name__ == "__main__":
    run()
