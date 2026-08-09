-- 07_create_indexes.sql
-- Performance indexes for efficient queries

SET search_path TO movie_night, public;

-- Users table indexes
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Groups table indexes
CREATE INDEX IF NOT EXISTS idx_groups_created_by ON groups(created_by);
CREATE INDEX IF NOT EXISTS idx_groups_created_at ON groups(created_at DESC);

-- Group members indexes
CREATE INDEX IF NOT EXISTS idx_group_members_user ON group_members(user_id);
CREATE INDEX IF NOT EXISTS idx_group_members_group ON group_members(group_id);

-- Movies table indexes
CREATE INDEX IF NOT EXISTS idx_movies_title ON movies(title);
CREATE INDEX IF NOT EXISTS idx_movies_release_date ON movies(release_date DESC);
CREATE INDEX IF NOT EXISTS idx_movies_tmdb_rating ON movies(tmdb_rating DESC);
CREATE INDEX IF NOT EXISTS idx_movies_popularity ON movies(popularity DESC);
CREATE INDEX IF NOT EXISTS idx_movies_runtime ON movies(runtime);

-- GIN index for array columns (genres, cast, keywords)
CREATE INDEX IF NOT EXISTS idx_movies_genres_gin ON movies USING GIN(genres);
CREATE INDEX IF NOT EXISTS idx_movies_cast_gin ON movies USING GIN(cast_names);
CREATE INDEX IF NOT EXISTS idx_movies_keywords_gin ON movies USING GIN(keywords);

-- JSONB index for streaming providers
CREATE INDEX IF NOT EXISTS idx_movies_streaming_gin ON movies USING GIN(streaming_providers);

-- Ratings table indexes
CREATE INDEX IF NOT EXISTS idx_ratings_user ON ratings(user_id);
CREATE INDEX IF NOT EXISTS idx_ratings_movie ON ratings(movie_id);
CREATE INDEX IF NOT EXISTS idx_ratings_rating ON ratings(rating DESC);
CREATE INDEX IF NOT EXISTS idx_ratings_created_at ON ratings(created_at DESC);

-- Composite index for finding user's rating for a specific movie
CREATE INDEX IF NOT EXISTS idx_ratings_user_movie ON ratings(user_id, movie_id);

-- Watchlist table indexes
CREATE INDEX IF NOT EXISTS idx_watchlist_group ON watchlist_items(group_id);
CREATE INDEX IF NOT EXISTS idx_watchlist_movie ON watchlist_items(movie_id);
CREATE INDEX IF NOT EXISTS idx_watchlist_watched ON watchlist_items(watched);
CREATE INDEX IF NOT EXISTS idx_watchlist_priority ON watchlist_items(priority DESC);
CREATE INDEX IF NOT EXISTS idx_watchlist_added_by ON watchlist_items(added_by);

-- Composite index for unwatched movies in a group (common query pattern)
CREATE INDEX IF NOT EXISTS idx_watchlist_group_unwatched 
    ON watchlist_items(group_id, watched) 
    WHERE watched = FALSE;

-- Recommendations table indexes
CREATE INDEX IF NOT EXISTS idx_recommendations_group ON recommendations(group_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_movie ON recommendations(movie_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_score ON recommendations(similarity_score DESC);
CREATE INDEX IF NOT EXISTS idx_recommendations_created_at ON recommendations(created_at DESC);

-- Movie reviews indexes
CREATE INDEX IF NOT EXISTS idx_reviews_movie ON movie_reviews(movie_id);
CREATE INDEX IF NOT EXISTS idx_reviews_created_at ON movie_reviews(created_at DESC);

-- Full-text search index on movie overview (optional for text search)
CREATE INDEX IF NOT EXISTS idx_movies_overview_fts 
    ON movies USING GIN(to_tsvector('english', overview));

CREATE INDEX IF NOT EXISTS idx_movies_title_fts 
    ON movies USING GIN(to_tsvector('english', title));

COMMENT ON INDEX idx_movies_overview_fts IS 'Full-text search on movie overview';
COMMENT ON INDEX idx_movies_title_fts IS 'Full-text search on movie title';

-- Analyze tables to update statistics for query planner
ANALYZE users;
ANALYZE groups;
ANALYZE group_members;
ANALYZE movies;
ANALYZE movie_embeddings;
ANALYZE ratings;
ANALYZE watchlist_items;
ANALYZE recommendations;
ANALYZE movie_reviews;

-- Display index information
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'movie_night'
ORDER BY tablename, indexname;
