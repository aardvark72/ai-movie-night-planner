-- AI Movie Night Planner - Seed Data
-- Test users, groups, and sample data for development

-- Set search path
SET search_path TO movie_night, public;

-- ============================================================================
-- USERS
-- Create test users for development and testing
-- ============================================================================

INSERT INTO movie_night.users (username, email, display_name, created_at) VALUES
    ('alice_smith', 'alice.smith@example.com', 'Alice Smith', NOW() - INTERVAL '90 days'),
    ('bob_jones', 'bob.jones@example.com', 'Bob Jones', NOW() - INTERVAL '75 days'),
    ('charlie_wilson', 'charlie.wilson@example.com', 'Charlie Wilson', NOW() - INTERVAL '60 days'),
    ('diana_martinez', 'diana.martinez@example.com', 'Diana Martinez', NOW() - INTERVAL '45 days'),
    ('eve_thompson', 'eve.thompson@example.com', 'Eve Thompson', NOW() - INTERVAL '30 days'),
    ('frank_garcia', 'frank.garcia@example.com', 'Frank Garcia', NOW() - INTERVAL '15 days')
ON CONFLICT (username) DO NOTHING;

-- ============================================================================
-- GROUPS
-- Create test viewing groups
-- ============================================================================

INSERT INTO movie_night.groups (group_name, description, created_by, created_at, is_active) VALUES
    (
        'Friday Night Crew',
        'Friends who meet every Friday evening to watch movies together',
        (SELECT user_id FROM movie_night.users WHERE username = 'alice_smith'),
        NOW() - INTERVAL '80 days',
        TRUE
    ),
    (
        'Family Movie Night',
        'Family-friendly movie selections for weekend viewing',
        (SELECT user_id FROM movie_night.users WHERE username = 'bob_jones'),
        NOW() - INTERVAL '70 days',
        TRUE
    ),
    (
        'Sci-Fi Enthusiasts',
        'Science fiction and fantasy movie lovers',
        (SELECT user_id FROM movie_night.users WHERE username = 'charlie_wilson'),
        NOW() - INTERVAL '50 days',
        TRUE
    ),
    (
        'Classic Cinema Club',
        'Exploring timeless classics from the golden age of Hollywood',
        (SELECT user_id FROM movie_night.users WHERE username = 'diana_martinez'),
        NOW() - INTERVAL '40 days',
        TRUE
    ),
    (
        'Horror Fans United',
        'For those who love a good scare',
        (SELECT user_id FROM movie_night.users WHERE username = 'eve_thompson'),
        NOW() - INTERVAL '25 days',
        TRUE
    )
ON CONFLICT DO NOTHING;

-- ============================================================================
-- GROUP MEMBERS
-- Assign users to groups with roles
-- ============================================================================

INSERT INTO movie_night.group_members (group_id, user_id, joined_at, role) VALUES
    -- Friday Night Crew (Alice is admin, others are members)
    (
        (SELECT group_id FROM movie_night.groups WHERE group_name = 'Friday Night Crew'),
        (SELECT user_id FROM movie_night.users WHERE username = 'alice_smith'),
        NOW() - INTERVAL '80 days',
        'admin'
    ),
    (
        (SELECT group_id FROM movie_night.groups WHERE group_name = 'Friday Night Crew'),
        (SELECT user_id FROM movie_night.users WHERE username = 'bob_jones'),
        NOW() - INTERVAL '78 days',
        'member'
    ),
    (
        (SELECT group_id FROM movie_night.groups WHERE group_name = 'Friday Night Crew'),
        (SELECT user_id FROM movie_night.users WHERE username = 'charlie_wilson'),
        NOW() - INTERVAL '75 days',
        'member'
    ),
    (
        (SELECT group_id FROM movie_night.groups WHERE group_name = 'Friday Night Crew'),
        (SELECT user_id FROM movie_night.users WHERE username = 'eve_thompson'),
        NOW() - INTERVAL '60 days',
        'member'
    ),
    
    -- Family Movie Night (Bob is admin)
    (
        (SELECT group_id FROM movie_night.groups WHERE group_name = 'Family Movie Night'),
        (SELECT user_id FROM movie_night.users WHERE username = 'bob_jones'),
        NOW() - INTERVAL '70 days',
        'admin'
    ),
    (
        (SELECT group_id FROM movie_night.groups WHERE group_name = 'Family Movie Night'),
        (SELECT user_id FROM movie_night.users WHERE username = 'diana_martinez'),
        NOW() - INTERVAL '68 days',
        'member'
    ),
    (
        (SELECT group_id FROM movie_night.groups WHERE group_name = 'Family Movie Night'),
        (SELECT user_id FROM movie_night.users WHERE username = 'frank_garcia'),
        NOW() - INTERVAL '15 days',
        'member'
    ),
    
    -- Sci-Fi Enthusiasts (Charlie is admin)
    (
        (SELECT group_id FROM movie_night.groups WHERE group_name = 'Sci-Fi Enthusiasts'),
        (SELECT user_id FROM movie_night.users WHERE username = 'charlie_wilson'),
        NOW() - INTERVAL '50 days',
        'admin'
    ),
    (
        (SELECT group_id FROM movie_night.groups WHERE group_name = 'Sci-Fi Enthusiasts'),
        (SELECT user_id FROM movie_night.users WHERE username = 'alice_smith'),
        NOW() - INTERVAL '48 days',
        'member'
    ),
    (
        (SELECT group_id FROM movie_night.groups WHERE group_name = 'Sci-Fi Enthusiasts'),
        (SELECT user_id FROM movie_night.users WHERE username = 'eve_thompson'),
        NOW() - INTERVAL '35 days',
        'member'
    ),
    
    -- Classic Cinema Club (Diana is admin)
    (
        (SELECT group_id FROM movie_night.groups WHERE group_name = 'Classic Cinema Club'),
        (SELECT user_id FROM movie_night.users WHERE username = 'diana_martinez'),
        NOW() - INTERVAL '40 days',
        'admin'
    ),
    (
        (SELECT group_id FROM movie_night.groups WHERE group_name = 'Classic Cinema Club'),
        (SELECT user_id FROM movie_night.users WHERE username = 'frank_garcia'),
        NOW() - INTERVAL '15 days',
        'member'
    ),
    
    -- Horror Fans United (Eve is admin)
    (
        (SELECT group_id FROM movie_night.groups WHERE group_name = 'Horror Fans United'),
        (SELECT user_id FROM movie_night.users WHERE username = 'eve_thompson'),
        NOW() - INTERVAL '25 days',
        'admin'
    ),
    (
        (SELECT group_id FROM movie_night.groups WHERE group_name = 'Horror Fans United'),
        (SELECT user_id FROM movie_night.users WHERE username = 'charlie_wilson'),
        NOW() - INTERVAL '22 days',
        'member'
    )
ON CONFLICT (group_id, user_id) DO NOTHING;

-- ============================================================================
-- SAMPLE MOVIES
-- Add a few sample movies to demonstrate the structure
-- (Real movie data will come from TMDB ingestion pipeline)
-- ============================================================================

INSERT INTO movie_night.movies (
    tmdb_id, 
    title, 
    original_title, 
    release_date, 
    runtime,
    overview, 
    tagline, 
    genres, 
    keywords,
    director, 
    cast_names,
    tmdb_rating, 
    tmdb_vote_count, 
    popularity,
    content_rating,
    poster_path,
    is_active
) VALUES
    (
        550,
        'Fight Club',
        'Fight Club',
        '1999-10-15',
        139,
        'A ticking-time-bomb insomniac and a slippery soap salesman channel primal male aggression into a shocking new form of therapy.',
        'Mischief. Mayhem. Soap.',
        ARRAY['Drama', 'Thriller', 'Action'],
        ARRAY['dual identity', 'rage and hate', 'nihilism', 'support group', 'cult'],
        'David Fincher',
        ARRAY['Brad Pitt', 'Edward Norton', 'Helena Bonham Carter', 'Meat Loaf', 'Jared Leto'],
        8.4,
        28542,
        89.234,
        'R',
        '/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg',
        TRUE
    ),
    (
        13,
        'Forrest Gump',
        'Forrest Gump',
        '1994-07-06',
        142,
        'A man with a low IQ has accomplished great things in his life and been present during significant historic events.',
        'The world will never be the same once you''ve seen it through the eyes of Forrest Gump.',
        ARRAY['Comedy', 'Drama', 'Romance'],
        ARRAY['vietnam war', 'vietnam veteran', 'mentally disabled', 'culture clash', 'hippie'],
        'Robert Zemeckis',
        ARRAY['Tom Hanks', 'Robin Wright', 'Gary Sinise', 'Mykelti Williamson', 'Sally Field'],
        8.5,
        26789,
        92.456,
        'PG-13',
        '/arw2vcBveWOVZr6pxd9XTd1TdQa.jpg',
        TRUE
    ),
    (
        603,
        'The Matrix',
        'The Matrix',
        '1999-03-31',
        136,
        'Set in the 22nd century, The Matrix tells the story of a computer hacker who joins a group of underground insurgents fighting the vast and powerful computers who now rule the earth.',
        'Welcome to the Real World.',
        ARRAY['Action', 'Science Fiction'],
        ARRAY['man vs machine', 'martial arts', 'dystopia', 'artificial intelligence', 'computer'],
        'Lana Wachowski',
        ARRAY['Keanu Reeves', 'Laurence Fishburne', 'Carrie-Anne Moss', 'Hugo Weaving', 'Joe Pantoliano'],
        8.2,
        24573,
        87.892,
        'R',
        '/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg',
        TRUE
    )
ON CONFLICT (tmdb_id) DO NOTHING;

-- ============================================================================
-- SAMPLE RATINGS
-- Add some sample ratings from users
-- ============================================================================

INSERT INTO movie_night.ratings (user_id, movie_id, rating, review_text, watched_date, rated_at) VALUES
    -- Alice's ratings
    (
        (SELECT user_id FROM movie_night.users WHERE username = 'alice_smith'),
        (SELECT movie_id FROM movie_night.movies WHERE tmdb_id = 550),
        4.5,
        'Mind-blowing! The twist at the end caught me completely off guard.',
        NOW() - INTERVAL '30 days',
        NOW() - INTERVAL '29 days'
    ),
    (
        (SELECT user_id FROM movie_night.users WHERE username = 'alice_smith'),
        (SELECT movie_id FROM movie_night.movies WHERE tmdb_id = 603),
        5.0,
        'A masterpiece of sci-fi cinema. Changed the game forever.',
        NOW() - INTERVAL '60 days',
        NOW() - INTERVAL '60 days'
    ),
    
    -- Bob's ratings
    (
        (SELECT user_id FROM movie_night.users WHERE username = 'bob_jones'),
        (SELECT movie_id FROM movie_night.movies WHERE tmdb_id = 13),
        5.0,
        'Beautiful story. Made me cry. Perfect for family viewing.',
        NOW() - INTERVAL '45 days',
        NOW() - INTERVAL '45 days'
    ),
    (
        (SELECT user_id FROM movie_night.users WHERE username = 'bob_jones'),
        (SELECT movie_id FROM movie_night.movies WHERE tmdb_id = 550),
        3.5,
        'Interesting but a bit too dark and violent for my taste.',
        NOW() - INTERVAL '35 days',
        NOW() - INTERVAL '34 days'
    ),
    
    -- Charlie's ratings
    (
        (SELECT user_id FROM movie_night.users WHERE username = 'charlie_wilson'),
        (SELECT movie_id FROM movie_night.movies WHERE tmdb_id = 603),
        5.0,
        'The best sci-fi movie ever made. Incredible action and deep philosophical themes.',
        NOW() - INTERVAL '50 days',
        NOW() - INTERVAL '50 days'
    ),
    
    -- Eve's ratings
    (
        (SELECT user_id FROM movie_night.users WHERE username = 'eve_thompson'),
        (SELECT movie_id FROM movie_night.movies WHERE tmdb_id = 550),
        4.5,
        'Dark, gritty, and thought-provoking. Loved the psychological aspects.',
        NOW() - INTERVAL '20 days',
        NOW() - INTERVAL '20 days'
    )
ON CONFLICT (user_id, movie_id) DO NOTHING;

-- ============================================================================
-- SUMMARY
-- ============================================================================

-- Count inserted records
DO $
DECLARE
    user_count INT;
    group_count INT;
    member_count INT;
    movie_count INT;
    rating_count INT;
BEGIN
    SELECT COUNT(*) INTO user_count FROM movie_night.users;
    SELECT COUNT(*) INTO group_count FROM movie_night.groups;
    SELECT COUNT(*) INTO member_count FROM movie_night.group_members;
    SELECT COUNT(*) INTO movie_count FROM movie_night.movies;
    SELECT COUNT(*) INTO rating_count FROM movie_night.ratings;
    
    RAISE NOTICE '=========================================';
    RAISE NOTICE 'Seed Data Summary';
    RAISE NOTICE '=========================================';
    RAISE NOTICE 'Users:          %', user_count;
    RAISE NOTICE 'Groups:         %', group_count;
    RAISE NOTICE 'Group Members:  %', member_count;
    RAISE NOTICE 'Movies:         %', movie_count;
    RAISE NOTICE 'Ratings:        %', rating_count;
    RAISE NOTICE '=========================================';
END $;
