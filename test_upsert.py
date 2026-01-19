# test_insert.py
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import insert
from db import SessionLocal
from models import RawEvent
from hashing import compute_content_hash
from sample_data import sample_gmail_event

def insert_sample():
    session = SessionLocal()

    event = sample_gmail_event("msg-001")
    content_hash = compute_content_hash(event["payload"])

    stmt = insert(RawEvent).values(
        id=None,
        source=event["source"],
        source_id=event["source_id"],
        occurred_at=event["occurred_at"],
        ingested_at=datetime.now(tz=timezone.utc),
        payload=event["payload"],
        content_hash=content_hash,
    ).on_conflict_do_update() # confirm only 1 row exist    
    # validates correctness under retries

    session.execute(stmt)
    session.commit()
    session.close()

if __name__ == "__main__":
    insert_sample()
    print("Inserted msg-001")
