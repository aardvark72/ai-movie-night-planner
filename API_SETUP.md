# API Setup Guide

Before running the TMDB ingestion pipeline, you only need **ONE API key**:

## TMDB API Key (Required)

### Get Your Key:
1. Go to https://www.themoviedb.org/
2. Create a free account (if you don't have one)
3. Go to Settings → API: https://www.themoviedb.org/settings/api
4. Request an API key (choose "Developer" option)
5. Fill out the application form (it's approved instantly)
6. Copy your API key

### Store in Databricks Secrets (Recommended):
```python
# In a notebook or terminal:
databricks secrets create-scope tmdb
databricks secrets put-secret tmdb api_key
# Paste your TMDB API key when prompted
```

### Or use temporary method:
Edit the notebook cell and paste your key directly (don't commit to git):
```python
TMDB_API_KEY = "your_tmdb_api_key_here"
```

## Embeddings - No Setup Required! 🎉

The pipeline now uses **Databricks Foundation Model APIs** for generating embeddings:
- ✅ **No external API key needed**
- ✅ Native Databricks integration
- ✅ Free with your workspace
- ✅ Uses `databricks-gte-large-en` model (1024 dimensions)
- ✅ Lower latency (stays within Databricks)

## Cost Estimate

### TMDB API:
- **Free**: 40 requests per 10 seconds
- No cost for any number of movies

### Databricks Embeddings:
- **Included with workspace** (Foundation Model APIs)
- No additional cost! 🎉

## Quick Start

1. Get your TMDB API key from: https://www.themoviedb.org/settings/api
2. Open the notebook: `01_tmdb_ingestion_pipeline`
3. In Cell 2 (TMDB API Configuration), replace the secrets line with:
   ```python
   TMDB_API_KEY = "your_key_here"
   ```
4. Run all cells! (No other API keys needed)

## Pipeline Configuration

The pipeline is currently configured to:
- Fetch movies from 2015-2024
- Minimum rating: 6.0/10
- Minimum votes: 100
- Process **50 movies** for initial testing
- Fetch 7 TMDB endpoints per movie (details, credits, keywords, providers, videos)
- Generate 1024-dim embeddings using Databricks GTE-large model

Edit the configuration in Cell 8 to adjust:
```python
START_YEAR = 2015
END_YEAR = 2024
MIN_RATING = 6.0
MAX_MOVIES_PER_YEAR = 100  # Per year
```

And in Cell 10 to control batch size:
```python
for i, movie_id in enumerate(unique_movie_ids[:50], 1):  # Change 50 to desired count
```

## Troubleshooting

### "Invalid API key" error:
- Double-check your TMDB API key is correct
- TMDB keys are 32 characters
- Make sure there are no extra spaces

### Rate limit errors:
- The pipeline includes automatic rate limiting
- If you still hit limits, increase `REQUEST_DELAY` in Cell 2

### Embedding errors:
- Ensure your workspace has access to Databricks Foundation Model APIs
- The `databricks-gte-large-en` endpoint should be available by default
