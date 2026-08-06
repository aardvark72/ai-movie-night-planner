# AI Movie Night Planner - Architecture & Planning

## Project Overview

The AI Movie Night Planner helps groups of users discover and select movies that everyone will enjoy. Users create viewing groups, rate movies individually, describe what they want to watch, and interact with an AI agent that recommends movies based on group preferences.

## Capstone Requirements ✅

1. **Data Pipeline (Spark)** - Ingest and process TMDB movie data
2. **Third-party API Integration** - TMDB API for movies, cast, reviews, streaming availability
3. **Unstructured Data Processing** - Embed plot summaries, reviews, cast info, keywords
4. **Databricks App** - Frontend for group management, browsing, agent interaction
5. **AI Agent with Tools** - Search/recommend movies AND write to database (ratings, watchlist, groups)

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATABRICKS APP                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │ Group Mgmt   │  │ Movie Browse │  │  Agent Chat UI       │ │
│  └──────────────┘  └──────────────┘  └──────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                         AI AGENT                                │
│  Tools: search_movies, add_to_watchlist, record_rating,        │
│         get_group_preferences, explain_recommendation           │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┴────────────────────┐
        ▼                                         ▼
┌──────────────────┐                    ┌──────────────────────┐
│ VECTOR SEARCH    │                    │   LAKEBASE POSTGRES  │
│ (Databricks)     │                    │                      │
│                  │                    │  Tables:             │
│ - Movie embeddings│                   │  • users             │
│ - Semantic search │                   │  • groups            │
│ - Filters         │                   │  • group_members     │
└──────────────────┘                    │  • movies            │
                                         │  • ratings           │
                                         │  • watchlist_items   │
                                         │  • recommendations   │
                                         └──────────────────────┘
                                                   ▲
                                                   │
┌──────────────────────────────────────────────────┘
│              SPARK DATA PIPELINE
│
│  1. Fetch from TMDB API (movies, cast, reviews, streaming)
│  2. Transform & clean data
│  3. Generate embeddings (plot + cast + reviews + keywords)
│  4. Load to Lakebase with vector columns
└─────────────────────────────────────────────────────────────────┘
```

---

*Note: For complete detailed documentation on each component, see the corresponding sections below or refer to the original architecture notebook.*

## Key Architectural Decisions

### 1. Lakebase Postgres with pgvector (vs. Databricks Vector Search)
* **Single source of truth**: Relational + vector data in same database
* **HNSW index**: Fast approximate nearest neighbor search
* **Native SQL joins**: Between vector similarity results and relational data
* **Simpler architecture**: No separate vector search service to manage

### 2. OpenAI text-embedding-ada-002
* **1536 dimensions**: Standard for semantic search
* **Cost**: ~$1 per 10,000 movies (one-time)
* **Quality**: Excellent for movie content (plot, cast, keywords)

### 3. TMDB API Integration
* **7 endpoints**: discover, details, credits, keywords, reviews, videos, watch/providers
* **Rate limits**: 40 requests per 10 seconds (free tier)
* **Caching**: Store raw responses in JSONB column
* **Target**: 5,000-10,000 movies for capstone

### 4. Agent Framework
* **6 tools**: 3 READ (search, get_preferences, explain) + 3 WRITE (add_watchlist, rate, compare)
* **Framework options**: LangChain or Databricks Mosaic AI Agent Framework
* **LLM options**: Databricks DBRX, GPT-4, or Claude

---

## Database Schema Summary

See `database/schema.sql` for full DDL.

**7 Tables:**
1. `users` - User profiles
2. `groups` - Viewing groups
3. `group_members` - Many-to-many user-group relationship
4. `movies` - Movie metadata + embeddings (vector column)
5. `ratings` - User ratings (0.5-5.0 stars)
6. `watchlist_items` - Group watchlists
7. `recommendations` - Agent recommendation history with explanations

**Key Features:**
* Postgres arrays for genres, cast, keywords
* JSONB for streaming providers and raw API data
* vector(1536) column for embeddings
* HNSW index on embedding column
* Foreign key constraints with CASCADE deletes

---

## TMDB API Integration Strategy

### Phase 1: Initial Seed (One-time)
1. Discover popular movies (past 10 years, rating ≥ 6.0)
2. Enrich each with: details, credits, keywords, providers, videos
3. Generate embeddings from combined text
4. Load to Lakebase

### Phase 2: Incremental Updates
* Weekly: New releases
* Monthly: Streaming availability updates
* On-demand: User-requested movies

---

## Vector Search & Embedding Strategy

### Embedding Content Template
```python
embedding_text = f"""
Title: {title}
Plot: {overview}
Genres: {', '.join(genres)}
Director: {director}
Cast: {', '.join(top_cast)}
Keywords: {', '.join(keywords)}
Tagline: {tagline}
"""
```

### Semantic Search Workflow
1. User query → Extract semantic intent + filters
2. Generate query embedding
3. Postgres: Vector similarity + WHERE filters
4. Agent: Rank by group preferences
5. Return top N with explanations

### Ranking Formula
```python
final_score = (
    0.5 * semantic_similarity(query_embedding, movie_embedding)
    + 0.3 * group_preference_match(group_profile, movie)
    - 0.2 * genre_penalty(disliked_genres)
)
```

---

## AI Agent Architecture

### Tool Definitions

| Tool | Type | Purpose |
|------|------|--------|
| `search_movies` | READ | Semantic search with filters |
| `get_group_preferences` | READ | Analyze viewing history |
| `explain_recommendation` | READ | Why a movie was recommended |
| `add_to_watchlist` | WRITE | Add movie to group watchlist |
| `record_rating` | WRITE | Record user rating after watching |
| `compare_movies` | READ | Compare multiple options |

### Agent Conversation Example
```
User: "We want to watch something tonight. Action but not scary."
Agent: [searches + ranks by group preferences]
Agent: "I found 3 great options..."
  1. Mad Max: Fury Road (Netflix, 120min, 8.1/10)
  2. Spider-Man: Into the Spider-Verse (Hulu, 117min, 8.4/10)
  3. The Bourne Identity (Prime, 119min, 7.9/10)

User: "Let's go with Spider-Verse!"
Agent: [adds to watchlist]
Agent: "Great choice! Enjoy! Let me know how it was."
```

---

## Databricks App Structure

### Technology
* **Framework**: Streamlit
* **Backend**: Python + psycopg2 / sqlalchemy
* **Agent**: LangChain or Mosaic AI

### Pages
1. Home / Dashboard
2. Group Management
3. Movie Browser (grid view + filters)
4. **Agent Chat** (core feature)
5. Watchlist
6. My Ratings

---

## Implementation Roadmap

### Week 1: Data Foundation
* Lakebase setup (database, schema, pgvector)
* TMDB ingestion pipeline
* Embedding generation
* Load to Lakebase

### Week 2: Agent Development
* Implement 6 agent tools
* Agent framework setup
* Context engineering (group preferences)
* Testing

### Week 3: App Frontend
* Streamlit app scaffolding
* Pages: groups, browse, watchlist, ratings
* **Agent chat UI** (priority)
* Database integration

### Week 4: Polish & Demo
* End-to-end testing
* UI/UX polish
* Documentation
* Demo preparation

---

## Success Criteria

✅ 5,000+ movies with embeddings in Lakebase  
✅ TMDB integration (5+ endpoints)  
✅ Semantic search working (pgvector)  
✅ Agent with READ + WRITE tools  
✅ Deployed Databricks App  
✅ End-to-end demo  

---

## Next Steps

**Phase 1 starts here:**
1. Create Lakebase Postgres project
2. Run `database/schema.sql` to create tables
3. Build TMDB ingestion pipeline (`notebooks/01_tmdb_ingestion_pipeline.py`)
4. Generate embeddings (`notebooks/02_embedding_generation.py`)
5. Load data and test vector search

For complete implementation details, see the notebooks and code in this repository.