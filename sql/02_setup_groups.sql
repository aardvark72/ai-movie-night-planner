-- 02_setup_groups.sql
-- Groups and group membership tables

SET search_path TO movie_night, public;

-- Groups table
CREATE TABLE IF NOT EXISTS groups (
    group_id SERIAL PRIMARY KEY,
    group_name VARCHAR(255) NOT NULL,
    description TEXT,
    created_by INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE groups IS 'Movie night groups';
COMMENT ON COLUMN groups.group_id IS 'Primary key - auto-incrementing group ID';
COMMENT ON COLUMN groups.group_name IS 'Display name for the group';
COMMENT ON COLUMN groups.created_by IS 'User who created the group (foreign key to users)';

-- Group members junction table
CREATE TABLE IF NOT EXISTS group_members (
    group_id INTEGER NOT NULL REFERENCES groups(group_id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_admin BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (group_id, user_id)
);

COMMENT ON TABLE group_members IS 'Many-to-many relationship between groups and users';
COMMENT ON COLUMN group_members.is_admin IS 'Whether this member has admin privileges in the group';

-- Insert sample groups
INSERT INTO groups (group_name, description, created_by) VALUES
    ('Friday Movie Night', 'Weekly movie night with friends', 1),
    ('Sci-Fi Fans', 'For lovers of science fiction', 2)
ON CONFLICT DO NOTHING;

-- Add members to groups
INSERT INTO group_members (group_id, user_id, is_admin) VALUES
    (1, 1, TRUE),  -- Alice is admin of Friday Movie Night
    (1, 2, FALSE), -- Bob is member
    (1, 3, FALSE), -- Charlie is member
    (2, 2, TRUE),  -- Bob is admin of Sci-Fi Fans
    (2, 1, FALSE)  -- Alice is member
ON CONFLICT DO NOTHING;

-- View groups with member counts
SELECT 
    g.group_id,
    g.group_name,
    g.description,
    u.display_name AS created_by_name,
    COUNT(gm.user_id) AS member_count
FROM groups g
JOIN users u ON g.created_by = u.user_id
LEFT JOIN group_members gm ON g.group_id = gm.group_id
GROUP BY g.group_id, g.group_name, g.description, u.display_name
ORDER BY g.group_id;
