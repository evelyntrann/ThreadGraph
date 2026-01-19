# sample_data.py
from datetime import datetime, timezone
import uuid
# mimic real Gmail message

def sample_gmail_event(message_id: str):
    return {
        "source": "gmail",
        "source_id": message_id,
        "occurred_at": datetime(2026, 1, 14, 21, 2, tzinfo=timezone.utc),
        "payload": {
            "subject": "Re: Interview availability",
            "from": "cheryl@tcu.edu",
            "to": "you@tcu.edu",
            "snippet": "Are you available Tuesday or Thursday?",
            "thread_id": "thread-123",
        },
    }
