-- AI Movie Night Planner - Database Schema
-- Lakebase Postgres Database: movie_night
-- Schema: movie_night

-- Enable pgvector extension for vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Create dedicated schema
CREATE SCHEMA IF NOT EXISTS movie_night;

-- Set search path to prioritize movie_night schema
SET search_path TO movie_night, public;

-- ============================================================================
-- TABLE: users
-- Stores user profiles and preferences
-- ============================================================================
CREATE TABLE movie_night.users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP
);

-- ============================================================================
-- TABLE: groups
-- Viewing groups created by users
-- ============================================================================
CREATE TABLE movie_night.groups (
    group_id SERIAL PRIMARY KEY,
    group_name VARCHAR(200) NOT NULL,
    description TEXT,
    created_by INTEGER REFERENCES users(user_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- ============================================================================
-- TABLE: group_members
-- Many-to-many relationship between users and groups
-- ============================================================================
CREATE TABLE movie_night.group_members (
    group_member_id SERIAL PRIMARY KEY,
    group_id INTEGER REFERENCES groups(group_id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    role VARCHAR(20) DEFAULT 'member',  -- 'admin' or 'member'
    UNIQUE(group_id, user_id)
);

-- ============================================================================
-- TABLE: movies
-- Core movie data from TMDB with embeddings for semantic search
-- ============================================================================
CREATE TABLE movie_night.movies (
    movie_id SERIAL PRIMARY KEY,
    tmdb_id INTEGER UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    original_title VARCHAR(500),
    release_date DATE,
    runtime INTEGER,  -- minutes
    
    -- Content
    overview TEXT,  -- plot summary
    tagline VARCHAR(500),
    genres TEXT[],  -- array of genre names
    keywords TEXT[],  -- array of keywords
    
    -- Cast & Crew
    director VARCHAR(200),
    cast_names TEXT[],  -- top 10 cast members
    
    -- Ratings & Popularity
    tmdb_rating DECIMAL(3,1),
    tmdb_vote_count INTEGER,
    popularity DECIMAL(10,3),
    
    -- Content Ratings
    content_rating VARCHAR(20),  -- G, PG, PG-13, R, etc.
    
    -- Media
    poster_path VARCHAR(500),
    backdrop_path VARCHAR(500),
    trailer_url VARCHAR(500),
    
    -- Streaming Availability (US)
    streaming_providers JSONB,  -- {"Netflix": true, "Hulu": false, ...}
    
    -- Embeddings (for semantic search)
    content_embedding vector(1536),  -- plot + cast + keywords
    
    -- Metadata
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    raw_data JSONB  -- full TMDB response
);

-- Indexes for movies table
CREATE INDEX idx_movies_tmdb_id ON movie_night.movies(tmdb_id);
CREATE INDEX idx_movies_release_date ON movie_night.movies(release_date);
CREATE INDEX idx_movies_genres ON movie_night.movies USING GIN(genres);
CREATE INDEX idx_movies_content_embedding ON movie_night.movies USING hnsw(content_embedding vector_cosine_ops);

-- ============================================================================
-- TABLE: ratings
-- User ratings for movies
-- ============================================================================
CREATE TABLE movie_night.ratings (
    rating_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    movie_id INTEGER REFERENCES movies(movie_id) ON DELETE CASCADE,
    rating DECIMAL(2,1) CHECK (rating >= 0.5 AND rating <= 5.0),  -- 0.5 to 5.0 stars
    review_text TEXT,
    watched_date DATE,
    rated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, movie_id)
);

CREATE INDEX idx_ratings_user ON movie_night.ratings(user_id);
CREATE INDEX idx_ratings_movie ON movie_night.ratings(movie_id);

-- ============================================================================
-- TABLE: watchlist_items
-- Movies added to group watchlists
-- ============================================================================
CREATE TABLE movie_night.watchlist_items (
    watchlist_id SERIAL PRIMARY KEY,
    group_id INTEGER REFERENCES groups(group_id) ON DELETE CASCADE,
    movie_id INTEGER REFERENCES movies(movie_id) ON DELETE CASCADE,
    added_by INTEGER REFERENCES users(user_id),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    priority INTEGER DEFAULT 0,  -- higher = more important
    watched BOOLEAN DEFAULT FALSE,
    watched_date DATE,
    notes TEXT,
    UNIQUE(group_id, movie_id)
);

CREATE INDEX idx_watchlist_group ON movie_night.watchlist_items(group_id);
CREATE INDEX idx_watchlist_watched ON movie_night.watchlist_items(watched);

-- ============================================================================
-- TABLE: recommendations
-- Agent-generated recommendations with explanations
-- ============================================================================
CREATE TABLE movie_night.recommendations (
    recommendation_id SERIAL PRIMARY KEY,
    group_id INTEGER REFERENCES groups(group_id) ON DELETE CASCADE,
    movie_id INTEGER REFERENCES movies(movie_id) ON DELETE CASCADE,
    user_query TEXT,  -- what the user asked for
    score DECIMAL(5,4),  -- recommendation confidence 0-1
    explanation TEXT,  -- why this movie was recommended
    recommended_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accepted BOOLEAN,  -- did they add it to watchlist?
    accepted_at TIMESTAMP
);

CREATE INDEX idx_recommendations_group ON movie_night.recommendations(group_id);
CREATE INDEX idx_recommendations_date ON movie_night.recommendations(recommended_at);

-- ============================================================================
-- SUMMARY
-- ============================================================================
-- Total tables: 7
-- - users: User accounts
-- - groups: Viewing groups
-- - group_members: User-group membership (many-to-many)
-- - movies: Movie metadata + embeddings (VECTOR COLUMN)
-- - ratings: User movie ratings
-- - watchlist_items: Group watchlists
-- - recommendations: Agent recommendation history
--
-- Key features:
-- - pgvector extension enabled
-- - HNSW index on movie embeddings for fast similarity search
-- - Postgres arrays for genres, keywords, cast
-- - JSONB for streaming providers and raw API data
-- - Foreign key constraints with CASCADE deletes
-- ============================================================================