# AI Movie Night Planner - Setup Guide

## ✅ Completed: Database Schema

All SQL schema files have been created and are ready to run!

### 📁 SQL Files Created

| File | Description | Tables/Objects |
|------|-------------|----------------|
| `00_setup_schema.sql` | Create schema + enable pgvector | movie_night schema, vector extension |
| `01_setup_users.sql` | User profiles | users, sample users |
| `02_setup_groups.sql` | Movie night groups | groups, group_members, sample groups |
| `03_setup_movies.sql` | Movie metadata | movies, movie_reviews, sample movies |
| `04_setup_ratings.sql` | User ratings | ratings, views for stats |
| `05_setup_watchlist.sql` | Group watchlists | watchlist_items, recommendations, views |
| `06_setup_embeddings.sql` | Vector embeddings | movie_embeddings, search functions |
| `07_create_indexes.sql` | Performance indexes | All performance indexes |

### 📓 Setup Notebook Created

**`notebooks/00_setup_schema`** - Automated setup notebook that:
- Connects to Lakebase
- Runs all SQL files in order
- Verifies schema creation
- Shows sample data counts

## 🚀 Quick Start

### Option 1: Run Setup Notebook (Recommended)

1. Open `notebooks/00_setup_schema` in Databricks
2. Attach to any cluster
3. Run all cells

### Option 2: Run SQL Files Manually

Connect to your Lakebase instance and run in order:

```sql
-- 1. Create schema and enable pgvector
\i sql/00_setup_schema.sql

-- 2. Create all tables
\i sql/01_setup_users.sql
\i sql/02_setup_groups.sql
\i sql/03_setup_movies.sql
\i sql/04_setup_ratings.sql
\i sql/05_setup_watchlist.sql
\i sql/06_setup_embeddings.sql

-- 3. Create indexes
\i sql/07_create_indexes.sql
```

## 📊 Database Schema Overview

```
movie_night (schema)
├── users                    # User profiles
├── groups                   # Movie night groups
├── group_members            # Group membership (junction)
├── movies                   # Movie metadata from TMDB
├── movie_reviews            # Reviews for sentiment analysis
├── movie_embeddings         # Vector embeddings (pgvector)
├── ratings                  # User ratings (0-5 scale)
├── watchlist_items          # Group watchlists
└── recommendations          # AI-generated recommendations
```

### Key Features

✅ **pgvector Support** - Vector similarity search for semantic movie discovery

✅ **Sample Data** - Pre-populated with test users, groups, movies, and ratings

✅ **Performance Indexes** - GIN indexes on arrays, B-tree on common queries, IVFFlat on vectors

✅ **Views & Functions** - Helper views for stats, PostgreSQL functions for semantic search

✅ **Foreign Keys** - Proper referential integrity with cascading deletes

## 🔍 Key SQL Functions

### Semantic Search

```sql
-- Search movies by semantic similarity
SELECT * FROM search_movies_semantic(
    query_embedding,  -- vector(1024) from embedding model
    10               -- limit
);
```

### Group Recommendations

```sql
-- Get recommendations for a group (excludes watched)
SELECT * FROM recommend_for_group(
    1,                -- group_id
    query_embedding,  -- vector(1024)
    5,                -- limit
    TRUE              -- exclude_watched
);
```

## 📈 Sample Data Included

After running the setup, you'll have:

* **3 Users**: Alice, Bob, Charlie
* **2 Groups**: "Friday Movie Night" (3 members), "Sci-Fi Fans" (2 members)
* **3 Movies**: Fight Club, Forrest Gump, Pulp Fiction
* **6 Ratings**: Various user ratings with reviews
* **4 Watchlist Items**: Mix of watched and unwatched

## ⚙️ Database Configuration

### Required Extensions

* **pgvector** - Vector similarity search (automatically enabled by `00_setup_schema.sql`)

### Connection Settings

The schema uses:
* **Search path**: `movie_night, public`
* **Vector dimensions**: 1024 (matching Databricks GTE-large model)
* **Distance metric**: Cosine distance (`<=>` operator)

## 🧪 Verification Queries

```sql
SET search_path TO movie_night, public;

-- Check all tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'movie_night'
ORDER BY table_name;

-- Check sample data
SELECT COUNT(*) FROM users;           -- Should be 3
SELECT COUNT(*) FROM groups;          -- Should be 2
SELECT COUNT(*) FROM movies;          -- Should be 3
SELECT COUNT(*) FROM ratings;         -- Should be 6
SELECT COUNT(*) FROM watchlist_items; -- Should be 4

-- Check pgvector extension
SELECT * FROM pg_extension WHERE extname = 'vector';

-- View sample ratings
SELECT 
    u.display_name,
    m.title,
    r.rating,
    r.review_text
FROM ratings r
JOIN users u ON r.user_id = u.user_id
JOIN movies m ON r.movie_id = m.movie_id
ORDER BY r.created_at DESC;
```

## 🎯 Next Steps

Now that the database schema is set up, continue with:

### 1. Get TMDB API Key
* Sign up at https://www.themoviedb.org
* Request API key (free for educational use)
* Run `setup_secrets.py` to store it

### 2. Ingest Movies from TMDB
* Run `notebooks/01_ingest_tmdb_movies.py`
* Fetches popular/top-rated movies
* Populates movies table with metadata

### 3. Generate Embeddings
* Run `notebooks/02_generate_embeddings.py`
* Creates vector embeddings using Databricks Foundation Model API
* Enables semantic search

### 4. Build Flask App
* Create `app.py` with REST API endpoints
* Implement agent tools
* Add semantic search

### 5. Deploy Databricks App
* Point app to Git folder
* Deploy via UI or CLI
* Test endpoints

## 📚 Resources

* **TMDB API**: https://developer.themoviedb.org/docs
* **pgvector**: https://github.com/pgvector/pgvector
* **Databricks Foundation Models**: https://docs.databricks.com/en/machine-learning/foundation-models/
* **Day 2 Boilerplate**: `/Workspace/Users/jrowan1972@gmail.com/databricks-lakebase-app-day-2/`

## 🐛 Troubleshooting

### pgvector extension not found
```sql
-- Install pgvector extension
CREATE EXTENSION vector;
```

### Permission denied on schema
```sql
-- Grant permissions to your role
GRANT ALL ON SCHEMA movie_night TO your_role_name;
```

### Connection issues
* Verify Lakebase instance is running
* Check connection URL secret: `database/movie-lakebase-url`
* Ensure native password authentication is enabled

---

Built with ❤️ for Databricks Capstone Project
