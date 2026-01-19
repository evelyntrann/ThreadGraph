from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from db import get_db
from models import RawEvent
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime, timezone
from fastapi import HTTPException

from hashing import compute_content_hash

app = FastAPI()

@app.post("/admin/events")
def create_events(
    event: dict, 
    db: Session = Depends(get_db)
):
    content_hash = compute_content_hash(event["payload"])
    stmt = insert(RawEvent).values(
        source=event["source"],
        source_id=event["source_id"],
        occurred_at=event["occurred_at"],
        ingested_at=datetime.now(tz=timezone.utc),
        payload=event["payload"],
        content_hash=content_hash,
    ).on_conflict_do_nothing()

    db.execute(stmt)
    db.commit()
    return {"status":"created"}



@app.get("/events/recent")
def get_recent_events(
    limit: int = 10, # this is the limit 
    db: Session = Depends(get_db)
):
    events = (
        db.query(RawEvent)
        .order_by(RawEvent.occurred_at.desc())
        .limit(limit) # limit is 10
        .all()
    )

    return [
        {
            "source": e.source,
            "source_id": e.source_id,
            "occurred_at": e.occurred_at,
            "payload": e.payload,
        }

        for e in events
    ]

@app.delete("/admin/events/{source}/{source_id}")
def delete_event(
    source: str,
    source_id: str,
    db: Session = Depends(get_db)
):
    deleted = (
        db.query(RawEvent)
        .filter(
            RawEvent.source == source,
            RawEvent.source_id == source_id
        )
        .delete()
    )

    db.commit()

    if deleted == 0:
        raise HTTPException(status_code=404, detail="Event not found")

    return {"status": "deleted"}
