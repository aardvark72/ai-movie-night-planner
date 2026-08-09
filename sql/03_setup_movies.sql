-- 03_setup_movies.sql
-- Movies table with metadata from TMDB

SET search_path TO movie_night, public;

CREATE TABLE IF NOT EXISTS movies (
    movie_id INTEGER PRIMARY KEY,  -- TMDB movie ID
    title VARCHAR(500) NOT NULL,
    original_title VARCHAR(500),
    release_date DATE,
    runtime INTEGER,  -- minutes
    overview TEXT,
    tagline TEXT,
    genres TEXT[],  -- Array of genre names
    director VARCHAR(255),
    cast_names TEXT[],  -- Top cast members (array)
    keywords TEXT[],  -- TMDB keywords (array)
    poster_path VARCHAR(255),  -- Path to poster image on TMDB
    backdrop_path VARCHAR(255),  -- Path to backdrop image on TMDB
    tmdb_rating DECIMAL(3, 1),  -- Average rating from TMDB (0-10)
    tmdb_vote_count INTEGER,
    popularity DECIMAL(10, 3),  -- TMDB popularity score
    budget BIGINT,
    revenue BIGINT,
    trailer_url TEXT,
    imdb_id VARCHAR(20),
    streaming_providers JSONB,  -- JSON object: {provider: link}
    original_language VARCHAR(10),
    adult BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE movies IS 'Movie metadata from TMDB API';
COMMENT ON COLUMN movies.movie_id IS 'TMDB movie ID (primary key)';
COMMENT ON COLUMN movies.genres IS 'Array of genre names (Action, Comedy, etc.)';
COMMENT ON COLUMN movies.cast_names IS 'Array of top cast member names';
COMMENT ON COLUMN movies.keywords IS 'Array of TMDB keyword tags';
COMMENT ON COLUMN movies.streaming_providers IS 'JSON map of streaming services to watch links';
COMMENT ON COLUMN movies.tmdb_rating IS 'Average user rating from TMDB (0-10 scale)';

-- Movie reviews table (optional - for embedding review sentiment)
CREATE TABLE IF NOT EXISTS movie_reviews (
    review_id SERIAL PRIMARY KEY,
    movie_id INTEGER NOT NULL REFERENCES movies(movie_id) ON DELETE CASCADE,
    author VARCHAR(255),
    content TEXT NOT NULL,
    rating DECIMAL(2, 1),  -- Individual review rating (if provided)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(50) DEFAULT 'tmdb'
);

COMMENT ON TABLE movie_reviews IS 'Movie reviews from TMDB (used for sentiment embedding)';
COMMENT ON COLUMN movie_reviews.source IS 'Source of review (tmdb, user, etc.)';

-- Sample movies for testing (will be replaced by TMDB ingestion)
INSERT INTO movies (movie_id, title, release_date, runtime, overview, genres, tmdb_rating, tmdb_vote_count) VALUES
    (550, 'Fight Club', '1999-10-15', 139, 'A ticking-time-bomb insomniac and a slippery soap salesman channel primal male aggression into a shocking new form of therapy.', 
     ARRAY['Drama', 'Thriller', 'Comedy'], 8.4, 26280),
    (13, 'Forrest Gump', '1994-07-06', 142, 'A man with a low IQ has accomplished great things in his life and been present during significant historic events.', 
     ARRAY['Comedy', 'Drama', 'Romance'], 8.5, 24918),
    (680, 'Pulp Fiction', '1994-10-14', 154, 'A burger-loving hit man, his philosophical partner, a drug-addled gangster''s moll and a washed-up boxer converge in this sprawling crime caper.', 
     ARRAY['Thriller', 'Crime'], 8.5, 25818)
ON CONFLICT (movie_id) DO NOTHING;

SELECT movie_id, title, release_date, runtime, genres, tmdb_rating 
FROM movies 
ORDER BY tmdb_rating DESC;
