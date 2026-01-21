from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
# import Session from sqlalchemy ORM for database connection
# make sure that the application can read/ write data accordingly
from db import get_db
from models import RawEvent, Extraction # import RawEvent model, which is Python class that represents the database table structure
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime, timezone
from fastapi import HTTPException #import exception class for returning HTTP errors

from hashing import compute_content_hash # unique custom class to create hashing 
# this will prevents data duplication, ensure data quality

app = FastAPI()

@app.post("/admin/events") # POST endpoint
def create_events(
    event: dict, 
    db: Session = Depends(get_db)
): # request to be dictionary/json object
    content_hash = compute_content_hash(event["payload"])
    stmt = insert(RawEvent).values(
        source=event["source"], # set the source column to the value from the incoming data
        source_id=event["source_id"], # set the source_id column to the value 
        occurred_at=event["occurred_at"], # when the events is actually happen
        ingested_at=datetime.now(tz=timezone.utc), # timestamp when this API receive the events
        payload=event["payload"],
        content_hash=content_hash,
    ).on_conflict_do_nothing()

    db.execute(stmt) # execute and prepare the insert statement against the database
    db.commit() # finalize the save operation and make sure the event is ready for querying
    return {"status":"created"}


# 
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
# DELETE endpoint with two paths parameters: source and source_id
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
    ) # query events need to delete

    db.commit()

    if deleted == 0: # if we cannot find the event
        raise HTTPException(status_code=404, detail="Event not found") # then raise error

    return {"status": "deleted"} # return this if deletion is occurred

# create this endpoint for inserting test data
@app.post("extraction")
def create_extraction(
    payload: dict, 
    db: Session = Depends(get_db)
):
    event_id = payload["event_id"]

    event = db.query(RawEvent).filter(RawEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="RawEvent not found")
    
    stmt = insert(Extraction).values(
        event_id=event_id,
        method="rule",
        extracted_at=datetime.now(tz=timezone.utc),
        confidence=payload.get("confidence", 0.7),
        data=payload["data"],
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

    return {"status" : "extraction update"}

# context endpoint, this does not call any LLM, but it reads from raw_event + extraction
# it returns the Context Pack like JSON
@app.post("/context")
def build_context(
    request: dict, 
    db: Session = Depends(get_db)
):
    query = request["query"]
    rows = (
        db.query(RawEvent, Extraction)
        .outerjoin(Extraction, Extraction.event_id == RawEvent.id)
        .order_by(RawEvent.occurred_at.desc()) # most recent to least recent
        .limit(20)
        .all()
    )

    facts = []
    actions = []

    for event, ext in rows:
        if ext is None: 
            continue

        if ext.data.get("is_promo"):
            continue

        facts.append({
            "text": event.payload.get("snippet"),
            "source": f"{event.source}:{event.source_id}",
            "occurred_at": event.occurred_at,
            "confidence": ext.confidence,
        })

        for a in ext.data.get("action_items", []):
            actions.append({
                "text": a,
                "source": f"{event.source}:{event.source_id}",
                "confidence": ext.confidence,
            })

    return {
        "query": query,
        "facts": facts,
        "open_actions": actions,
    }
# at this point, we get: raw_event  →  extraction  →  context


