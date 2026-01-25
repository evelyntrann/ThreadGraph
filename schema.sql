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

CREATE TABLE IF NOT EXISTS extraction (
  id UUID PRIMARY KEY,
  event_id UUID REFERENCES raw_event(id) ON DELETE CASCADE,
  method TEXT NOT NULL,              -- "rule"
  extracted_at TIMESTAMPTZ NOT NULL,
  confidence FLOAT NOT NULL,
  data JSONB NOT NULL,
  UNIQUE (event_id, method)
);

CREATE INDEX IF NOT EXISTS idx_extraction_event_id
ON extraction(event_id);

CREATE INDEX IF NOT EXISTS idx_extraction_data
ON extraction USING GIN (data);

CREATE TABLE IF NOT EXISTS embedding (
  id UUI PRIMARY_KEY,
  object_type TEXT NOT NULL,
  object_id UUID NOT NULL,
  model TEXT NOT NULL,
  vector VECTOR(1536) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_embedding_object
ON embedding(object_type, object_id);

CREATE INDEX idx_embedding_vector 
ON embedding using ivfflat (vector vector_cosine_ops);
