-- ThreadGraph Database Schema

-- Create the raw_event table for storing events
CREATE TABLE IF NOT EXISTS raw_event (
  id UUID PRIMARY KEY,
  source TEXT NOT NULL,
  source_id TEXT NOT NULL,
  occurred_at TIMESTAMPTZ NOT NULL,
  ingested_at TIMESTAMPTZ NOT NULL,
  payload JSONB NOT NULL,
  content_hash BYTEA NOT NULL,
  UNIQUE (source, source_id)
);

-- Optional: Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_raw_event_source ON raw_event(source);
CREATE INDEX IF NOT EXISTS idx_raw_event_occurred_at ON raw_event(occurred_at);
CREATE INDEX IF NOT EXISTS idx_raw_event_ingested_at ON raw_event(ingested_at);
