# 🎬 AI Movie Night Planner

An intelligent movie recommendation system that helps groups discover and select movies everyone will enjoy.

## 🌟 Project Overview

The AI Movie Night Planner combines Databricks Apps, Lakebase Postgres, vector search, and AI agents to create a collaborative movie selection experience. Users create viewing groups, rate movies, and interact with an AI agent that provides personalized recommendations based on group preferences and semantic understanding.

## ✅ Capstone Requirements

This project fulfills all capstone requirements:

* **Data Pipeline (Spark)** - Ingest and process movie data from TMDB API
* **Third-party API Integration** - TMDB API for movies, cast, reviews, streaming availability
* **Unstructured Data Processing** - Embeddings over plot summaries, cast info, reviews, keywords
* **Databricks App** - Full-featured frontend with group management and agent chat
* **AI Agent with Tools** - Agent with both read (search/explain) and write (ratings/watchlist) capabilities

## 🏗️ Architecture

```
Databricks App (Streamlit)
    ↓
AI Agent (6 tools: search, recommend, add_to_watchlist, rate, explain, compare)
    ↓
Lakebase Postgres + pgvector (relational tables + embeddings)
    ↑
Spark Pipeline → TMDB API → Embedding Generation
```

### Key Components

* **Lakebase Postgres**: 7 tables (users, groups, group_members, movies, ratings, watchlist_items, recommendations)
* **Vector Search**: pgvector with HNSW index for semantic movie search
* **TMDB Integration**: 7 API endpoints (discover, details, credits, keywords, reviews, videos, providers)
* **AI Agent**: 6 tools for searching, explaining, and modifying data

## 📁 Repository Structure

```
ai-movie-night-planner/
├── README.md                          # This file
├── .gitignore                         # Git ignore rules
├── architecture.md                    # Detailed architecture documentation
├── notebooks/
│   ├── 01_tmdb_ingestion_pipeline.py  # Fetch and process TMDB data
│   ├── 02_embedding_generation.py     # Generate movie embeddings
│   └── 03_agent_testing.py            # Test agent tools
├── database/
│   ├── schema.sql                     # Database schema (CREATE TABLE statements)
│   └── seed_data.sql                  # Sample users/groups for testing
├── agent/
│   ├── movie_agent.py                 # Main agent logic
│   ├── tools.py                       # Agent tool definitions
│   └── prompts.py                     # System prompts
├── app/
│   ├── app.py                         # Main Streamlit app
│   ├── app.yaml                       # App configuration
│   ├── requirements.txt               # Python dependencies
│   └── pages/
│       ├── 1_browse_movies.py
│       ├── 2_groups.py
│       ├── 3_watchlist.py
│       ├── 4_agent_chat.py            # Main agent interaction page
│       └── 5_my_ratings.py
└── utils/
    ├── db.py                          # Lakebase connection utilities
    ├── tmdb_client.py                 # TMDB API wrapper
    └── embeddings.py                  # Embedding generation utilities
```

## 🚀 Getting Started

### Prerequisites

* Databricks workspace with Serverless compute
* Lakebase Postgres project
* TMDB API key (free, requires registration at https://www.themoviedb.org/settings/api)
* OpenAI API key (for embeddings)

### Setup Steps

1. **Clone this repository** in Databricks
   ```bash
   # Already done if you're reading this!
   ```

2. **Set up Lakebase database**
   ```sql
   -- Run database/schema.sql to create all tables
   ```

3. **Configure secrets**
   ```python
   # Store API keys in Databricks secrets
   dbutils.secrets.put(scope="api-keys", key="tmdb_api_key", string_value="your_key")
   dbutils.secrets.put(scope="api-keys", key="openai_api_key", string_value="your_key")
   ```

4. **Run data pipeline**
   ```bash
   # Execute notebooks/01_tmdb_ingestion_pipeline.py
   # Then notebooks/02_embedding_generation.py
   ```

5. **Deploy the app**
   ```bash
   cd app/
   databricks apps deploy movie-night-planner
   ```

## 🎯 Features

### User Features
* Create and manage viewing groups
* Rate movies you've watched
* Add movies to group watchlists
* Browse movies with filters (genre, year, streaming service)
* View personal rating history

### AI Agent Capabilities
* **Semantic Search**: "Find a funny sci-fi movie that isn't too violent"
* **Group Preferences**: Analyzes past ratings to understand group taste
* **Smart Recommendations**: Ranks by semantic similarity + group preferences
* **Explanations**: Explains why each movie was recommended
* **Comparisons**: Compare multiple movies for group decision-making
* **Actions**: Add to watchlist, record ratings, mark as watched

## 🛠️ Technology Stack

* **Frontend**: Streamlit (Databricks App)
* **Database**: Lakebase Postgres with pgvector extension
* **Data Processing**: Apache Spark (PySpark)
* **Vector Search**: pgvector HNSW index
* **Embeddings**: OpenAI text-embedding-ada-002 (1536 dimensions)
* **LLM**: Databricks DBRX / GPT-4 / Claude
* **Agent Framework**: LangChain or Databricks Mosaic AI Agent Framework
* **APIs**: TMDB v3 API

## 📊 Database Schema

### Core Tables
* `users` - User profiles
* `groups` - Viewing groups
* `group_members` - User-group membership (many-to-many)
* `movies` - Movie metadata with embeddings (vector column)
* `ratings` - User movie ratings
* `watchlist_items` - Group watchlists
* `recommendations` - Agent recommendation history

See `database/schema.sql` for full DDL.

## 🤖 Agent Tools

1. **search_movies** (READ) - Semantic search with filters
2. **get_group_preferences** (READ) - Analyze group viewing history
3. **add_to_watchlist** (WRITE) - Add movie to group watchlist
4. **record_rating** (WRITE) - Record user rating after watching
5. **explain_recommendation** (READ) - Detailed recommendation explanation
6. **compare_movies** (READ) - Compare multiple options

## 📝 Development Roadmap

* **Week 1**: Data foundation (Lakebase setup, TMDB ingestion, embeddings)
* **Week 2**: Agent development (tools, framework, testing)
* **Week 3**: App frontend (Streamlit UI, agent chat)
* **Week 4**: Polish and demo preparation

See `architecture.md` for detailed implementation plan.

## 📄 License

This project is for educational purposes as part of a Databricks capstone project.

## 🙏 Acknowledgments

* Movie data provided by [The Movie Database (TMDB)](https://www.themoviedb.org/)
* "This product uses the TMDB API but is not endorsed or certified by TMDB."

## 👤 Author

Created as a capstone project demonstrating Databricks Apps, Lakebase, Vector Search, and AI Agents.

---

**Status**: 🚧 In Development

Current Phase: Setting up repository structure and initial architecture