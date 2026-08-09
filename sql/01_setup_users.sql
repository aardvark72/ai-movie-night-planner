-- 01_setup_users.sql
-- Users table for authentication and profiles

SET search_path TO movie_night, public;

CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE users IS 'User profiles for movie night groups';
COMMENT ON COLUMN users.user_id IS 'Primary key - auto-incrementing user ID';
COMMENT ON COLUMN users.username IS 'Unique username for login';
COMMENT ON COLUMN users.email IS 'Unique email address';
COMMENT ON COLUMN users.display_name IS 'Display name shown in UI';

-- Insert sample users for testing
INSERT INTO users (username, email, display_name) VALUES
    ('alice', 'alice@example.com', 'Alice Johnson'),
    ('bob', 'bob@example.com', 'Bob Smith'),
    ('charlie', 'charlie@example.com', 'Charlie Davis')
ON CONFLICT (username) DO NOTHING;

SELECT * FROM users;
