-- Add search_vector column if it doesn't exist
ALTER TABLE submission 
ADD COLUMN IF NOT EXISTS search_vector tsvector;

-- Create or replace function to update search_vector
CREATE OR REPLACE FUNCTION submission_search_vector_update() 
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := to_tsvector('english', 
        coalesce(NEW.title, '') || ' ' || 
        coalesce(NEW.selftext, '') || ' ' || 
        coalesce(NEW.submission_id, '')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop trigger if exists and recreate
DROP TRIGGER IF EXISTS submission_search_vector_trigger ON submission;

CREATE TRIGGER submission_search_vector_trigger
BEFORE INSERT OR UPDATE ON submission
FOR EACH ROW
EXECUTE FUNCTION submission_search_vector_update();

-- Update existing rows
UPDATE submission SET search_vector = to_tsvector('english', 
    coalesce(title, '') || ' ' || 
    coalesce(selftext, '') || ' ' || 
    coalesce(submission_id, '')
);

-- Create GIN index for fast full-text search
CREATE INDEX IF NOT EXISTS idx_submission_search ON submission USING GIN(search_vector);
