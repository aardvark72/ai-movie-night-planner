-- 05_setup_watchlist.sql
-- Group watchlists and recommendations

SET search_path TO movie_night, public;

-- Group watchlist table
CREATE TABLE IF NOT EXISTS watchlist_items (
    watchlist_id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES groups(group_id) ON DELETE CASCADE,
    movie_id INTEGER NOT NULL REFERENCES movies(movie_id) ON DELETE CASCADE,
    added_by INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    priority INTEGER DEFAULT 0,  -- For sorting/ranking movies
    watched BOOLEAN DEFAULT FALSE,
    watched_date DATE,
    notes TEXT,  -- Group notes about the movie
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (group_id, movie_id)  -- One entry per movie per group
);

COMMENT ON TABLE watchlist_items IS 'Group watchlists - movies groups want to watch';
COMMENT ON COLUMN watchlist_items.priority IS 'Higher priority = watch sooner (user-defined ranking)';
COMMENT ON COLUMN watchlist_items.watched IS 'Whether the group has watched this movie';
COMMENT ON COLUMN watchlist_items.notes IS 'Group notes or comments about the movie';

-- AI-generated recommendations table
CREATE TABLE IF NOT EXISTS recommendations (
    recommendation_id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES groups(group_id) ON DELETE CASCADE,
    movie_id INTEGER NOT NULL REFERENCES movies(movie_id) ON DELETE CASCADE,
    recommendation_reason TEXT NOT NULL,  -- AI-generated explanation
    similarity_score DECIMAL(5, 4),  -- Vector similarity score (0-1)
    prompt TEXT,  -- Original user prompt that generated this recommendation
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE recommendations IS 'AI-generated movie recommendations for groups';
COMMENT ON COLUMN recommendations.recommendation_reason IS 'AI explanation of why this movie was recommended';
COMMENT ON COLUMN recommendations.similarity_score IS 'Vector similarity score from semantic search';
COMMENT ON COLUMN recommendations.prompt IS 'The natural language prompt used to generate this recommendation';

-- Insert sample watchlist items
INSERT INTO watchlist_items (group_id, movie_id, added_by, priority, watched, watched_date) VALUES
    (1, 550, 1, 10, TRUE, '2024-02-01'),  -- Friday Movie Night watched Fight Club
    (1, 13, 2, 5, FALSE, NULL),           -- Forrest Gump is on the list
    (1, 680, 1, 8, FALSE, NULL),          -- Pulp Fiction is on the list
    (2, 680, 2, 10, TRUE, '2024-01-28')   -- Sci-Fi Fans watched Pulp Fiction
ON CONFLICT (group_id, movie_id) DO NOTHING;

-- View: Group watchlist with movie details
CREATE OR REPLACE VIEW group_watchlist_view AS
SELECT 
    w.watchlist_id,
    g.group_id,
    g.group_name,
    m.movie_id,
    m.title,
    m.release_date,
    m.runtime,
    m.genres,
    m.tmdb_rating,
    w.watched,
    w.watched_date,
    w.priority,
    u.display_name AS added_by_name,
    w.created_at AS added_at
FROM watchlist_items w
JOIN groups g ON w.group_id = g.group_id
JOIN movies m ON w.movie_id = m.movie_id
JOIN users u ON w.added_by = u.user_id
ORDER BY g.group_id, w.watched, w.priority DESC, w.created_at DESC;

-- View: Unwatched movies by group
CREATE OR REPLACE VIEW unwatched_movies_by_group AS
SELECT 
    g.group_id,
    g.group_name,
    COUNT(*) AS unwatched_count,
    ARRAY_AGG(m.title ORDER BY w.priority DESC) AS movies
FROM groups g
JOIN watchlist_items w ON g.group_id = w.group_id
JOIN movies m ON w.movie_id = m.movie_id
WHERE w.watched = FALSE
GROUP BY g.group_id, g.group_name
ORDER BY unwatched_count DESC;

SELECT * FROM group_watchlist_view;
SELECT * FROM unwatched_movies_by_group;
