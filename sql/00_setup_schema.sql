-- 00_setup_schema.sql
-- Create the movie_night schema and enable pgvector extension

-- Create schema
CREATE SCHEMA IF NOT EXISTS movie_night;

-- Set search path for this session
SET search_path TO movie_night, public;

-- Enable pgvector extension (required for vector similarity search)
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify extension is installed
SELECT * FROM pg_extension WHERE extname = 'vector';

COMMENT ON SCHEMA movie_night IS 'AI Movie Night Planner - Group movie recommendations with semantic search';
