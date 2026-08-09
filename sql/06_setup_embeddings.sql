-- 06_setup_embeddings.sql
-- Movie embeddings for semantic search using pgvector

SET search_path TO movie_night, public;

-- Movie embeddings table with pgvector
CREATE TABLE IF NOT EXISTS movie_embeddings (
    movie_id INTEGER PRIMARY KEY REFERENCES movies(movie_id) ON DELETE CASCADE,
    content_embedding vector(1024),  -- Combined: plot + keywords + cast + genres
    plot_embedding vector(1024),     -- Just plot summary (overview + tagline)
    review_embedding vector(1024),   -- Aggregated review sentiment (optional)
    embedding_model VARCHAR(100) DEFAULT 'databricks-gte-large',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE movie_embeddings IS 'Vector embeddings for semantic movie search';
COMMENT ON COLUMN movie_embeddings.content_embedding IS 'Combined embedding: plot + keywords + cast + genres (1024 dims)';
COMMENT ON COLUMN movie_embeddings.plot_embedding IS 'Plot-only embedding: overview + tagline (1024 dims)';
COMMENT ON COLUMN movie_embeddings.review_embedding IS 'Aggregated review sentiment embedding (1024 dims)';
COMMENT ON COLUMN movie_embeddings.embedding_model IS 'Model used to generate embeddings (e.g., databricks-gte-large)';

-- Create index for vector similarity search (using cosine distance)
-- This enables fast nearest-neighbor search
CREATE INDEX IF NOT EXISTS movie_content_embedding_idx 
    ON movie_embeddings 
    USING ivfflat (content_embedding vector_cosine_ops)
    WITH (lists = 100);

CREATE INDEX IF NOT EXISTS movie_plot_embedding_idx 
    ON movie_embeddings 
    USING ivfflat (plot_embedding vector_cosine_ops)
    WITH (lists = 100);

COMMENT ON INDEX movie_content_embedding_idx IS 'IVFFlat index for fast cosine similarity search on content embeddings';
COMMENT ON INDEX movie_plot_embedding_idx IS 'IVFFlat index for fast cosine similarity search on plot embeddings';

-- Example query function for semantic search
-- Usage: SELECT * FROM search_movies_semantic('funny sci-fi movie under 2 hours', 10);
CREATE OR REPLACE FUNCTION search_movies_semantic(
    query_embedding vector(1024),
    result_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    movie_id INTEGER,
    title VARCHAR(500),
    release_date DATE,
    runtime INTEGER,
    genres TEXT[],
    overview TEXT,
    tmdb_rating DECIMAL(3, 1),
    similarity_score DECIMAL(5, 4)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        m.movie_id,
        m.title,
        m.release_date,
        m.runtime,
        m.genres,
        m.overview,
        m.tmdb_rating,
        (1 - (e.content_embedding <=> query_embedding))::DECIMAL(5, 4) AS similarity_score
    FROM movies m
    JOIN movie_embeddings e ON m.movie_id = e.movie_id
    WHERE e.content_embedding IS NOT NULL
    ORDER BY e.content_embedding <=> query_embedding
    LIMIT result_limit;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION search_movies_semantic IS 'Semantic search for movies using vector similarity (cosine distance)';

-- Example: Group recommendation query (excludes already-watched movies)
CREATE OR REPLACE FUNCTION recommend_for_group(
    target_group_id INTEGER,
    query_embedding vector(1024),
    result_limit INTEGER DEFAULT 5,
    exclude_watched BOOLEAN DEFAULT TRUE
)
RETURNS TABLE (
    movie_id INTEGER,
    title VARCHAR(500),
    release_date DATE,
    runtime INTEGER,
    genres TEXT[],
    overview TEXT,
    tmdb_rating DECIMAL(3, 1),
    similarity_score DECIMAL(5, 4),
    is_watched BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    WITH group_watched AS (
        SELECT w.movie_id
        FROM watchlist_items w
        WHERE w.group_id = target_group_id AND w.watched = TRUE
    ),
    group_preferences AS (
        SELECT 
            AVG(r.rating) AS avg_rating_threshold
        FROM ratings r
        JOIN group_members gm ON r.user_id = gm.user_id
        WHERE gm.group_id = target_group_id
    )
    SELECT 
        m.movie_id,
        m.title,
        m.release_date,
        m.runtime,
        m.genres,
        m.overview,
        m.tmdb_rating,
        (1 - (e.content_embedding <=> query_embedding))::DECIMAL(5, 4) AS similarity_score,
        EXISTS(SELECT 1 FROM group_watched gw WHERE gw.movie_id = m.movie_id) AS is_watched
    FROM movies m
    JOIN movie_embeddings e ON m.movie_id = e.movie_id
    CROSS JOIN group_preferences gp
    WHERE 
        e.content_embedding IS NOT NULL
        AND m.tmdb_rating >= COALESCE(gp.avg_rating_threshold, 6.0)
        AND (NOT exclude_watched OR m.movie_id NOT IN (SELECT movie_id FROM group_watched))
    ORDER BY e.content_embedding <=> query_embedding
    LIMIT result_limit;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION recommend_for_group IS 'Recommend movies for a group based on semantic similarity and preferences, excluding watched movies';

-- Note: Actual embeddings will be populated by the Spark notebook (02_generate_embeddings.py)
-- which uses Databricks Foundation Model API to generate vectors
SELECT 
    COUNT(*) AS total_movies,
    COUNT(e.content_embedding) AS movies_with_embeddings,
    ROUND(100.0 * COUNT(e.content_embedding) / COUNT(*), 2) AS embedding_coverage_percent
FROM movies m
LEFT JOIN movie_embeddings e ON m.movie_id = e.movie_id;
