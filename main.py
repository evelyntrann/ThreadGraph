from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from db import get_db
from models import RawEvent

app = FastAPI()

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