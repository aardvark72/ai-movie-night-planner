# API Setup Guide

Before running the TMDB ingestion pipeline, you need to configure two API keys:

## 1. TMDB API Key (Required)

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

## 2. OpenAI API Key (Required for Embeddings)

### Get Your Key:
1. Go to https://platform.openai.com/api-keys
2. Sign up or log in
3. Create a new API key
4. Copy the key (you won't see it again!)

### Store in Databricks Secrets (Recommended):
```python
databricks secrets create-scope openai
databricks secrets put-secret openai api_key
# Paste your OpenAI API key when prompted
```

### Or use temporary method:
Edit the embedding cell and add:
```python
openai_api_key = "your_openai_api_key_here"
```

## Cost Estimate

### TMDB API:
- **Free**: 40 requests per 10 seconds
- No cost for any number of movies

### OpenAI Embeddings (text-embedding-ada-002):
- **$0.0001 per 1,000 tokens**
- Average movie: ~500 tokens
- **50 movies ≈ $0.03**
- **1,000 movies ≈ $0.50**
- **5,000 movies ≈ $2.50**

## Quick Start (Without Secrets)

If you want to test immediately without setting up secrets:

1. Open the notebook: `01_tmdb_ingestion_pipeline`
2. In Cell 2 (TMDB API Configuration), replace the secrets line with:
   ```python
   TMDB_API_KEY = "your_key_here"
   ```
3. In Cell 5 (Embedding Generation), add after the imports:
   ```python
   openai_api_key = "your_key_here"
   ```
4. Run all cells!

## Pipeline Configuration

The pipeline is currently configured to:
- Fetch movies from 2015-2024
- Minimum rating: 6.0/10
- Minimum votes: 100
- Process **50 movies** for initial testing
- Fetch 7 TMDB endpoints per movie (details, credits, keywords, providers, videos)

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
- Double-check your API key is correct
- TMDB keys are 32 characters
- Make sure there are no extra spaces

### Rate limit errors:
- The pipeline includes automatic rate limiting
- If you still hit limits, increase `REQUEST_DELAY` in Cell 2

### OpenAI quota errors:
- Check your OpenAI account has credits: https://platform.openai.com/usage
- New accounts get $5 free credit
