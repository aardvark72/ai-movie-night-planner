-- 04_setup_ratings.sql
-- User movie ratings and reviews

SET search_path TO movie_night, public;

CREATE TABLE IF NOT EXISTS ratings (
    rating_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    movie_id INTEGER NOT NULL REFERENCES movies(movie_id) ON DELETE CASCADE,
    rating DECIMAL(2, 1) NOT NULL CHECK (rating >= 0 AND rating <= 5),
    review_text TEXT,
    watched_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, movie_id)  -- One rating per user per movie
);

COMMENT ON TABLE ratings IS 'User ratings and reviews for movies';
COMMENT ON COLUMN ratings.rating IS 'User rating on 0-5 scale';
COMMENT ON COLUMN ratings.watched_date IS 'Date the user watched the movie';
COMMENT ON CONSTRAINT ratings_rating_check ON ratings IS 'Ratings must be between 0 and 5';

-- Insert sample ratings
INSERT INTO ratings (user_id, movie_id, rating, review_text, watched_date) VALUES
    (1, 550, 5.0, 'Mind-blowing! Changed how I think about consumerism.', '2024-01-15'),
    (1, 13, 4.5, 'Heartwarming and inspiring. Tom Hanks at his best.', '2024-01-20'),
    (2, 550, 4.0, 'Great movie but a bit dark for me.', '2024-01-16'),
    (2, 680, 5.0, 'Tarantino''s masterpiece. Love the non-linear storytelling.', '2024-01-18'),
    (3, 13, 5.0, 'Makes me cry every time. Beautiful story.', '2024-01-22'),
    (3, 680, 3.5, 'Good but too violent for my taste.', '2024-01-19')
ON CONFLICT (user_id, movie_id) DO NOTHING;

-- View: User ratings summary
CREATE OR REPLACE VIEW user_rating_stats AS
SELECT 
    u.user_id,
    u.display_name,
    COUNT(r.rating_id) AS movies_rated,
    ROUND(AVG(r.rating), 2) AS avg_rating,
    MAX(r.rating) AS max_rating,
    MIN(r.rating) AS min_rating
FROM users u
LEFT JOIN ratings r ON u.user_id = r.user_id
GROUP BY u.user_id, u.display_name
ORDER BY movies_rated DESC;

-- View: Movie ratings summary
CREATE OR REPLACE VIEW movie_rating_stats AS
SELECT 
    m.movie_id,
    m.title,
    COUNT(r.rating_id) AS user_rating_count,
    ROUND(AVG(r.rating), 2) AS avg_user_rating,
    m.tmdb_rating,
    m.tmdb_vote_count
FROM movies m
LEFT JOIN ratings r ON m.movie_id = r.movie_id
GROUP BY m.movie_id, m.title, m.tmdb_rating, m.tmdb_vote_count
ORDER BY user_rating_count DESC;

SELECT * FROM user_rating_stats;
SELECT * FROM movie_rating_stats;
