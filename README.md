# AI Movie Night Planner 🎬

An intelligent movie recommendation system that helps groups discover movies they'll all enjoy. Built with **Databricks**, **Lakebase Postgres**, **LangGraph**, and **Streamlit**.

## Overview

MovieMate is a conversational AI agent that:
- 🔍 **Searches movies** using semantic similarity (pgvector + GTE-large embeddings)
- 🎯 **Personalizes recommendations** based on group viewing history
- 📝 **Manages watchlists** with priority levels
- ⭐ **Tracks ratings** to improve future suggestions
- 💬 **Explains reasoning** behind recommendations
- ⚖️ **Compares movies** to help groups decide

## Architecture

```
┌─────────────────────────────────────────────────┐
│           Streamlit UI                          │
│  • Chat interface                               │
│  • Movie cards                                  │
│  • Watchlist management                         │
└───────────────────┬─────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│         MovieMate Agent (LangGraph)             │
│  • System prompt (personality + guidelines)     │
│  • Tool orchestration                           │
│  • Multi-turn conversation                      │
└───────────────────┬─────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
┌───────────────┐       ┌───────────────┐
│  READ Tools   │       │  WRITE Tools  │
├───────────────┤       ├───────────────┤
│ search_movies │       │ add_watchlist │
│ get_prefs     │       │ record_rating │
│ explain_rec   │       │ compare       │
└───────┬───────┘       └───────┬───────┘
        │                       │
        └───────────┬───────────┘
                    ▼
┌─────────────────────────────────────────────────┐
│     Lakebase Postgres + pgvector                │
│  • 53 movies with metadata                      │
│  • 50 movies with embeddings (1024-dim)         │
│  • User ratings & watchlists                    │
│  • Semantic search via vector similarity        │
└─────────────────────────────────────────────────┘
```

## Features

### 🤖 MovieMate Agent
- Friendly, conversational personality
- Understands group dynamics and preferences
- Explains why movies match your request
- Considers practical constraints (runtime, ratings)

### 🎬 Semantic Search
- Natural language queries: "epic space adventure with aliens"
- Vector similarity using pgvector extension
- GTE-large embeddings (1024 dimensions)
- Filters: runtime, rating, already-watched

### 👥 Group-Aware Recommendations
- Analyzes group viewing history
- Identifies top genres and favorite movies
- Balances different tastes
- Excludes already-watched movies

### 📝 Watchlist Management
- Add movies with priority levels (1-10)
- Personal notes for each movie
- Mark as watched
- Sort by priority or rating

### ⭐ Rating System
- Rate movies 0.5 to 5.0 stars
- Write reviews
- Improves future recommendations
- Track viewing history

## Project Structure

```
ai-movie-night-planner/
├── agent/                      # AI Agent
│   ├── __init__.py
│   ├── config.py              # System prompt & settings
│   ├── agent.py               # LangGraph orchestration
│   ├── tools.py               # 6 tool functions
│   ├── test_agent.py          # Validation tests
│   └── README.md
│
├── streamlit_app/             # Streamlit UI
│   ├── app.py                 # Main application
│   ├── components/
│   │   ├── __init__.py
│   │   ├── chat.py            # Chat interface
│   │   ├── movie_card.py      # Movie display
│   │   └── watchlist.py       # Watchlist UI
│   └── utils/
│       ├── __init__.py
│       └── session.py         # Session management
│
├── notebooks/                 # Development notebooks
│   ├── 01_setup_database.py
│   ├── 02_test_agent_tools.ipynb
│   └── 03_embed_and_load.py
│
├── app.yaml                   # Databricks App config
├── requirements.txt           # Python dependencies
├── DEPLOYMENT.md             # Deployment guide
└── README.md                 # This file
```

## Quick Start

### 1. Prerequisites

- Databricks workspace with Apps V2
- Lakebase Postgres instance
- OpenAI API key (for agent)

### 2. Set Up Database

Run the setup notebook to create tables and load data:

```python
# notebooks/01_setup_database.py
# Creates schema, loads movies, generates embeddings
```

### 3. Configure Secrets

```bash
databricks secrets put-secret \
  --scope <scope> \
  --key lakebase-connection-url \
  --string-value "<base64-encoded-url>"

databricks secrets put-secret \
  --scope <scope> \
  --key openai-api-key \
  --string-value "<your-key>"
```

### 4. Deploy

```bash
cd /Workspace/Users/<email>/ai-movie-night-planner
databricks apps deploy . --source-dir .
```

### 5. Use the App

Open the deployed app and start chatting:
- "Find me a comedy under 2 hours"
- "What should we watch tonight?"
- "Show me movies like Inception"

## Example Interactions

**User**: "We want something funny but not too long"

**MovieMate**: 
```
🎬 How about *Spirited*? It's a fun comedy-musical at 127 minutes - 
not too long for a movie night! It's got great energy and won't 
overstay its welcome. Want me to add it to your watchlist?
```

**User**: "Find me a space adventure like Interstellar"

**MovieMate**: (Calls get_group_preferences, then search_movies)
```
Based on your group's love of sci-fi, I think you'd enjoy:

1. **Kingdom of the Planet of the Apes** (2024)
   145 min | 7.1/10 | Sci-Fi, Adventure
   Epic scale and emotional depth similar to Interstellar

2. **Infinite** (2021)
   106 min | 6.6/10 | Sci-Fi, Action
   Mind-bending concepts and fast-paced action
```

## Technology Stack

- **Database**: Lakebase Postgres with pgvector extension
- **Embeddings**: Databricks GTE-large (1024-dim)
- **Agent**: LangGraph + LangChain + OpenAI GPT-4
- **UI**: Streamlit
- **Deployment**: Databricks Apps V2

## Development

### Running Locally

```bash
# Set environment variables
export LAKEBASE_CONNECTION_URL="<url>"
export OPENAI_API_KEY="<key>"

# Run Streamlit
cd streamlit_app
streamlit run app.py
```

### Testing Agent Tools

```python
from agent import chat

response = chat("Find me a comedy", group_id=1)
print(response)
```

### Adding New Movies

```python
# Use notebooks/03_embed_and_load.py
# Fetches from TMDB, generates embeddings, loads to DB
```

## Database Schema

### movies
- id, title, release_year, runtime_minutes
- tmdb_rating, overview, poster_url
- genres (JSONB), cast_names (JSONB)
- embedding (vector(1024))

### user_ratings
- user_id, movie_id, rating, review_text
- watched_date, created_at

### watchlist_items
- group_id, movie_id, added_by
- priority, notes, watched, added_at

### viewing_groups & group_members
- Group management tables

## Contributing

1. Add new movies to the database
2. Improve agent prompts in `agent/config.py`
3. Enhance UI components in `streamlit_app/components/`
4. Add new tools in `agent/tools.py`

## License

MIT License - see LICENSE file

## Support

For issues or questions:
- Check DEPLOYMENT.md for troubleshooting
- Review agent/README.md for agent details
- Test tools with notebooks/02_test_agent_tools.ipynb

---

Built with ❤️ using Databricks, Lakebase, LangGraph, and Streamlit
