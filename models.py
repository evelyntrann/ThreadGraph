# models.py
from sqlalchemy import Column, String, DateTime, JSON, LargeBinary, UniqueConstraint, ForeignKey, JSONB, Float
from sqlalchemy.dialects.postgresql import UUID
import uuid

from db import Base
# canonical data model
# this is the first table: raw_event: store metadata for the Gmail + Calendar events
class RawEvent(Base):
    __tablename__ = "raw_event"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String, nullable=False)
    source_id = Column(String, nullable=False)
    occurred_at = Column(DateTime(timezone=True), nullable=False) 
    ingested_at = Column(DateTime(timezone=True), nullable=False)
    payload = Column(JSON, nullable=False)
    content_hash = Column(LargeBinary, nullable=False) # for dedup/update

    # Unique constraint on (source, source_id)
    __table_args__ = (
        UniqueConstraint('source', 'source_id', name='raw_event_source_source_id_key'),
    )

class Extraction(Base): 
    __tablename__ = "extraction"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("raw_event.id"), nullable=False)
    method = Column(String, nullable=False)
    extracted_at = Column(DateTime(timezone=True))
    confidence = Column(Float, nullable=False)
    data = Column(JSONB, nullable=False)

    __table_args__ = (
        UniqueConstraint("event_id", "method", name="uq_event_method"),

    )

