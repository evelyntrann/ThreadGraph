from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
# import Session from sqlalchemy ORM for database connection
# make sure that the application can read/ write data accordingly
from db import get_db
from models import RawEvent # import RawEvent model, which is Python class that represents the database table structure
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

