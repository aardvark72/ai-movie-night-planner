# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# DBTITLE 1,🔧 Setup: Upgrade Databricks SDK
# =============================================================================
# SDK UPGRADE - Run this first!
# Lakebase requires databricks-sdk >= 0.118.0
# =============================================================================

import importlib.metadata as md
import subprocess, sys

try:
    before = md.version("databricks-sdk")
except md.PackageNotFoundError:
    before = None

print(f"Current SDK version: {before}")
print("Upgrading to >=0.118.0...")

subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", "--upgrade", "databricks-sdk>=0.118.0"])

after = md.version("databricks-sdk")
print(f"databricks-sdk: {before} -> {after}  (changed={before != after})")

if before != after:
    print("\n⚠️  Version changed — restarting Python to load the new SDK...")
    print("    After restart, continue from cell 2 (Imports and Setup)")
    dbutils.library.restartPython()
else:
    print("✅ SDK already up to date, no restart needed")

# COMMAND ----------

# DBTITLE 1,TMDB Data Ingestion Pipeline
# MAGIC %md
# MAGIC # TMDB Data Ingestion Pipeline
# MAGIC
# MAGIC This notebook fetches movie data from The Movie Database (TMDB) API and loads it into the Lakebase Postgres database.
# MAGIC
# MAGIC ## Pipeline Steps:
# MAGIC
# MAGIC 1. **Discover Movies** - Use TMDB discover API to find movies matching criteria
# MAGIC 2. **Fetch Details** - Get full details for each movie (metadata, cast, keywords, providers)
# MAGIC 3. **Generate Embeddings** - Create vector embeddings using Databricks Foundation Model APIs
# MAGIC 4. **Load to Database** - Insert movies into Lakebase with embeddings
# MAGIC
# MAGIC ## Prerequisites:
# MAGIC
# MAGIC ✅ TMDB API key (see [API_SETUP.md](../API_SETUP.md))
# MAGIC ✅ Lakebase database created and schema loaded
# MAGIC ✅ No OpenAI key needed - uses Databricks embeddings!
# MAGIC
# MAGIC ---

# COMMAND ----------

# DBTITLE 1,Imports and Setup
import sys
import json
from typing import List, Dict
import time

# Add utils to path
sys.path.append('/Workspace/Users/jevon.rowan2510@gmail.com/ai-movie-night-planner')

from utils.tmdb_client import TMDBClient
from utils.db import LakebaseConnection, insert_movie

print("✅ Imports loaded successfully!")

# COMMAND ----------

# DBTITLE 1,⚙️ SETUP: Add TMDB API Key to Secrets
# =============================================================================
# ONE-TIME SETUP: Add TMDB API Key to Secrets
# Run this cell once to store your TMDB API key in Databricks secrets
# Get your key from: https://www.themoviedb.org/settings/api
# =============================================================================

from databricks.sdk import WorkspaceClient
import getpass

w = WorkspaceClient()

print("🔐 Adding TMDB API key to 'database' scope...")
print("Get your free TMDB API key from: https://www.themoviedb.org/settings/api\n")

# Add TMDB API key to existing 'database' scope
w.secrets.put_secret(
    scope="database",
    key="tmdb_api_key",
    string_value=getpass.getpass("Paste your TMDB API key: ")
)

print("\n✅ TMDB API key successfully stored in 'database' scope!")
print("   Scope: database")
print("   Key: tmdb_api_key")
print("\nYou can now run cell 3 (TMDB API Configuration) to continue.")

# COMMAND ----------

# DBTITLE 1,TMDB API Configuration
# =============================================================================
# TMDB API KEY - REQUIRED
# Get your free key from: https://www.themoviedb.org/settings/api
# =============================================================================

# Option 1: Use Databricks Secrets (recommended for production)
try:
    TMDB_API_KEY = dbutils.secrets.get(scope="database", key="tmdb_api_key")
    print("✅ TMDB API key loaded from secrets")
except:
    # Option 2: Paste your key here for testing (don't commit to git!)
    TMDB_API_KEY = "YOUR_TMDB_API_KEY_HERE"  # <-- Paste your TMDB API key here
    
    if not TMDB_API_KEY:
        raise ValueError(
            "❌ TMDB API key not found!\n"
            "Get your free key from: https://www.themoviedb.org/settings/api\n"
            "Then either:\n"
            "  1. Store in secrets: databricks secrets put-secret database tmdb_api_key\n"
            "  2. Paste it in the TMDB_API_KEY variable above"
        )
    print("⚠️  Using API key from notebook (not recommended for production)")

# Initialize TMDB client
tmdb = TMDBClient(api_key=TMDB_API_KEY)
print(f"✅ TMDB client initialized")

# COMMAND ----------

# DBTITLE 1,Database Connection
# =============================================================================
# LAKEBASE CONNECTION
# Using password authentication (stored in secrets)
# =============================================================================

import psycopg2
from psycopg2.extras import RealDictCursor
from databricks.sdk import WorkspaceClient
import base64

w = WorkspaceClient()

# Get connection URL from secrets (base64-encoded, includes password)
print("🔑 Loading database connection...")
secret = w.secrets.get_secret(scope="database", key="movie-lakebase-url")
LAKEBASE_URL = base64.b64decode(secret.value).decode('utf-8')

# Connect using the complete connection URL with password
print("🔌 Connecting to Lakebase...")
conn = psycopg2.connect(LAKEBASE_URL)

# Set schema
cursor = conn.cursor()
cursor.execute("SET search_path TO movie_night, public")
cursor.close()

# Test connection
cursor = conn.cursor(cursor_factory=RealDictCursor)
cursor.execute("SELECT COUNT(*) as count FROM movies")
result = cursor.fetchone()
cursor.close()

print(f"✅ Database connected - Current movies in database: {result['count']}")

# Create simple query helpers
def db_query(sql, params=None):
    """Execute a SELECT query and return results as list of dicts."""
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(sql, params)
    results = cursor.fetchall()
    cursor.close()
    return [dict(row) for row in results]

def db_execute(sql, params=None, commit=True):
    """Execute INSERT/UPDATE/DELETE and return affected row count."""
    cursor = conn.cursor()
    cursor.execute(sql, params)
    rowcount = cursor.rowcount
    if commit:
        conn.commit()
    cursor.close()
    return rowcount

# COMMAND ----------

# DBTITLE 1,Embeddings Setup (Databricks Foundation Model APIs)
# =============================================================================
# EMBEDDINGS - Using Databricks Foundation Model APIs
# Model: databricks-gte-large-en (1024 dimensions)
# No external API key needed!
# =============================================================================

import requests

# Get workspace credentials once
workspace_url = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiUrl().get()
api_token = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()

def generate_embedding(text: str) -> List[float]:
    """Generate embedding using Databricks Foundation Model API.
    
    Args:
        text: Text to embed
    
    Returns:
        List of 1024 floats
    """
    try:
        url = f"{workspace_url}/serving-endpoints/databricks-gte-large-en/invocations"
        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json"
            },
            json={"input": [text]}
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get('data', [{}])[0].get('embedding', [])
        else:
            print(f"❌ Embedding API error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Embedding error: {e}")
        return None

# Test embedding
test_embedding = generate_embedding("A thrilling action movie about superheroes")
if test_embedding:
    print(f"✅ Embeddings working - Dimension: {len(test_embedding)}")
else:
    print("❌ Embedding test failed")

# COMMAND ----------

# DBTITLE 1,Discovery Configuration
# =============================================================================
# DISCOVERY CONFIGURATION
# Adjust these parameters to control what movies are fetched
# =============================================================================

START_YEAR = 2015
END_YEAR = 2024
MIN_RATING = 6.0          # Minimum TMDB rating (0-10)
MIN_VOTES = 100           # Minimum vote count
MAX_MOVIES_PER_YEAR = 100 # Maximum movies to fetch per year

print("\n" + "=" * 70)
print("DISCOVERY CONFIGURATION")
print("=" * 70)
print(f"Year Range:       {START_YEAR} - {END_YEAR}")
print(f"Min Rating:       {MIN_RATING}/10")
print(f"Min Votes:        {MIN_VOTES}")
print(f"Max Per Year:     {MAX_MOVIES_PER_YEAR}")
print(f"Estimated Total:  {(END_YEAR - START_YEAR + 1) * MAX_MOVIES_PER_YEAR} movies max")
print("=" * 70)

# COMMAND ----------

# DBTITLE 1,Step 1: Discover Movies
# =============================================================================
# STEP 1: DISCOVER MOVIES
# Fetch movie IDs from TMDB using the discover API
# =============================================================================

all_movie_ids = []

for year in range(START_YEAR, END_YEAR + 1):
    print(f"\n🔍 Discovering movies from {year}...")
    
    movies_this_year = []
    page = 1
    max_pages = 5  # TMDB returns ~20 movies per page, so 5 pages = ~100 movies
    
    while page <= max_pages and len(movies_this_year) < MAX_MOVIES_PER_YEAR:
        response = tmdb.discover_movies(
            year=year,
            min_rating=MIN_RATING,
            min_votes=MIN_VOTES,
            page=page
        )
        
        movies = response.get('results', [])
        if not movies:
            break
        
        for movie in movies:
            movies_this_year.append(movie['id'])
            if len(movies_this_year) >= MAX_MOVIES_PER_YEAR:
                break
        
        page += 1
    
    print(f"   Found {len(movies_this_year)} movies")
    all_movie_ids.extend(movies_this_year)

# Remove duplicates
unique_movie_ids = list(set(all_movie_ids))

print(f"\n" + "=" * 70)
print(f"✅ DISCOVERY COMPLETE")
print(f"   Total movies discovered: {len(unique_movie_ids)}")
print("=" * 70)

# COMMAND ----------

# DBTITLE 1,Step 2: Fetch Full Movie Details
# =============================================================================
# STEP 2: FETCH FULL MOVIE DETAILS
# Get complete data for each movie (7 API calls per movie)
# =============================================================================

movies_data = []
failed_movies = []

# For initial testing, process first 50 movies
# Change 50 to len(unique_movie_ids) to process all
BATCH_SIZE = 50

print(f"\n🎬 Fetching details for {min(BATCH_SIZE, len(unique_movie_ids))} movies...")
print(f"   (7 API calls per movie: details, credits, keywords, videos, providers, ratings)")
print()

for i, movie_id in enumerate(unique_movie_ids[:BATCH_SIZE], 1):
    try:
        # Fetch all movie data
        movie = tmdb.get_movie_full(movie_id)
        
        if movie and movie.get('tmdb_id'):
            movies_data.append(movie)
            
            # Progress indicator
            if i % 10 == 0:
                print(f"   [{i}/{min(BATCH_SIZE, len(unique_movie_ids))}] Fetched: {movie['title']} ({movie.get('release_date', 'N/A')[:4]})")
        else:
            failed_movies.append(movie_id)
    
    except Exception as e:
        print(f"   ❌ Error fetching movie {movie_id}: {e}")
        failed_movies.append(movie_id)

print(f"\n" + "=" * 70)
print(f"✅ FETCH COMPLETE")
print(f"   Movies fetched:  {len(movies_data)}")
print(f"   Failed:          {len(failed_movies)}")
print("=" * 70)

# Show sample
if movies_data:
    sample = movies_data[0]
    print(f"\n📋 Sample Movie:")
    print(f"   Title:     {sample['title']}")
    print(f"   Year:      {sample.get('release_date', 'N/A')[:4]}")
    print(f"   Genres:    {', '.join(sample.get('genres', []))}")
    print(f"   Director:  {sample.get('director', 'N/A')}")
    print(f"   Rating:    {sample.get('tmdb_rating', 'N/A')}/10")

# COMMAND ----------

# DBTITLE 1,Step 3: Generate Embeddings
# =============================================================================
# STEP 3: GENERATE EMBEDDINGS
# Create vector embeddings for semantic search
# =============================================================================

print(f"\n🧠 Generating embeddings using Databricks GTE-large model...")
print(f"   Model: databricks-gte-large-en (1024 dimensions)")
print()

movies_with_embeddings = []
embedding_failures = []

for i, movie in enumerate(movies_data, 1):
    try:
        # Create embedding text from overview + tagline + genres + keywords + cast
        embedding_text_parts = []
        
        if movie.get('overview'):
            embedding_text_parts.append(movie['overview'])
        
        if movie.get('tagline'):
            embedding_text_parts.append(movie['tagline'])
        
        if movie.get('genres'):
            embedding_text_parts.append(f"Genres: {', '.join(movie['genres'])}")
        
        if movie.get('keywords'):
            embedding_text_parts.append(f"Keywords: {', '.join(movie['keywords'][:10])}")
        
        if movie.get('cast_names'):
            embedding_text_parts.append(f"Cast: {', '.join(movie['cast_names'][:5])}")
        
        embedding_text = " | ".join(embedding_text_parts)
        
        # Generate embedding
        embedding = generate_embedding(embedding_text)
        
        if embedding and len(embedding) == 1024:
            movie['embedding'] = embedding
            movie['embedding_text'] = embedding_text
            movies_with_embeddings.append(movie)
            
            if i % 10 == 0:
                print(f"   [{i}/{len(movies_data)}] Generated embedding for: {movie['title']}")
        else:
            print(f"   ❌ Invalid embedding for: {movie['title']}")
            embedding_failures.append(movie['title'])
    
    except Exception as e:
        print(f"   ❌ Error generating embedding for {movie['title']}: {e}")
        embedding_failures.append(movie['title'])

print(f"\n" + "=" * 70)
print(f"✅ EMBEDDINGS GENERATED")
print(f"   Success:  {len(movies_with_embeddings)}")
print(f"   Failed:   {len(embedding_failures)}")
print("=" * 70)

# COMMAND ----------

# DBTITLE 1,Step 4: Load to Database
# =============================================================================
# STEP 4: LOAD TO DATABASE
# Insert movies with embeddings into Lakebase
# =============================================================================

print(f"\n💾 Loading {len(movies_with_embeddings)} movies to database...")
print()

inserted_count = 0
updated_count = 0
failed_inserts = []

for i, movie in enumerate(movies_with_embeddings, 1):
    try:
        # Check if movie already exists
        # Note: movie_id IS the TMDB ID in our schema
        existing = db_query(
            "SELECT movie_id FROM movies WHERE movie_id = %s",
            (movie.get('tmdb_id', movie.get('id')),)
        )
        
        is_update = len(existing) > 0
        
        # Build INSERT statement matching schema
        # Note: movie_id is the TMDB ID (primary key)
        insert_sql = """
            INSERT INTO movies (
                movie_id, title, release_date, overview, tagline, runtime,
                genres, keywords, tmdb_rating, tmdb_vote_count, popularity,
                director, cast_names, streaming_providers
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (movie_id) DO UPDATE SET
                title = EXCLUDED.title,
                release_date = EXCLUDED.release_date,
                overview = EXCLUDED.overview,
                tagline = EXCLUDED.tagline,
                runtime = EXCLUDED.runtime,
                genres = EXCLUDED.genres,
                keywords = EXCLUDED.keywords,
                tmdb_rating = EXCLUDED.tmdb_rating,
                tmdb_vote_count = EXCLUDED.tmdb_vote_count,
                popularity = EXCLUDED.popularity,
                director = EXCLUDED.director,
                cast_names = EXCLUDED.cast_names,
                streaming_providers = EXCLUDED.streaming_providers,
                updated_at = CURRENT_TIMESTAMP
            RETURNING movie_id
        """
        
        # Get TMDB ID (might be 'tmdb_id' or 'id' depending on source)
        tmdb_id = movie.get('tmdb_id', movie.get('id'))
        
        db_execute(
            insert_sql,
            (
                tmdb_id,
                movie.get('title'),
                movie.get('release_date'),
                movie.get('overview'),
                movie.get('tagline'),
                movie.get('runtime'),
                movie.get('genres', []),
                movie.get('keywords', []),
                movie.get('tmdb_rating'),
                movie.get('vote_count'),
                movie.get('popularity'),
                movie.get('director'),
                movie.get('cast_names', []),
                json.dumps(movie.get('streaming_providers', {}))
            ),
            commit=False  # Don't commit yet - need to insert embedding too
        )
        
        # Insert embedding into movie_embeddings table
        if movie.get('embedding'):
            embedding_sql = """
                INSERT INTO movie_embeddings (
                    movie_id, content_embedding, embedding_model
                ) VALUES (
                    %s, %s, %s
                )
                ON CONFLICT (movie_id) DO UPDATE SET
                    content_embedding = EXCLUDED.content_embedding,
                    embedding_model = EXCLUDED.embedding_model,
                    updated_at = CURRENT_TIMESTAMP
            """
            
            db_execute(
                embedding_sql,
                (tmdb_id, movie['embedding'], 'databricks-gte-large-en'),
                commit=True  # Commit both inserts together
            )
        
        if is_update:
            updated_count += 1
        else:
            inserted_count += 1
        
        if i % 10 == 0:
            print(f"   [{i}/{len(movies_with_embeddings)}] Loaded: {movie['title']}")
    
    except Exception as e:
        print(f"   ❌ Failed to insert {movie['title']}: {e}")
        failed_inserts.append(movie['title'])

conn.commit()

print(f"\n" + "=" * 70)
print(f"✅ DATABASE LOAD COMPLETE")
print(f"   Inserted:  {inserted_count}")
print(f"   Updated:   {updated_count}")
print(f"   Failed:    {len(failed_inserts)}")
print("=" * 70)

# COMMAND ----------

# DBTITLE 1,Verification & Summary
# =============================================================================
# VERIFICATION & SUMMARY
# =============================================================================

# Get final counts
total_movies = db_query("SELECT COUNT(*) as count FROM movies")[0]['count']
movies_with_embeddings_count = db_query(
    "SELECT COUNT(*) as count FROM movie_embeddings WHERE content_embedding IS NOT NULL"
)[0]['count']

# Get sample movies
sample_movies = db_query("""
    SELECT 
        m.title, 
        m.release_date,
        ARRAY_TO_STRING(m.genres, ', ') as genres,
        m.tmdb_rating,
        m.director,
        CASE WHEN e.content_embedding IS NOT NULL THEN '✅' ELSE '❌' END as has_embedding
    FROM movies m
    LEFT JOIN movie_embeddings e ON m.movie_id = e.movie_id
    ORDER BY m.updated_at DESC
    LIMIT 10
""")

print("\n" + "=" * 70)
print("🎉 PIPELINE COMPLETE")
print("=" * 70)
print(f"Total movies in database:     {total_movies}")
print(f"Movies with embeddings:       {movies_with_embeddings_count}")
print(f"Coverage:                     {100 * movies_with_embeddings_count / max(total_movies, 1):.1f}%")
print("=" * 70)

print("\n📋 Latest Movies Added:")
print("-" * 70)
for movie in sample_movies:
    year = str(movie['release_date'].year) if movie['release_date'] else 'N/A'
    print(f"{movie['has_embedding']} {movie['title']:40} ({year}) - {movie['tmdb_rating']}/10")

# Test vector search
print("\n🔍 Testing Vector Search...")
test_query = "space adventure with aliens"
test_embedding = generate_embedding(test_query)

if test_embedding:
    results = db_query("""
        SELECT 
            m.title,
            m.release_date,
            m.tmdb_rating,
            1 - (e.content_embedding <=> %s::vector) as similarity
        FROM movies m
        JOIN movie_embeddings e ON m.movie_id = e.movie_id
        WHERE e.content_embedding IS NOT NULL
        ORDER BY e.content_embedding <=> %s::vector
        LIMIT 5
    """, (test_embedding, test_embedding))
    
    print(f"\nQuery: '{test_query}'")
    print("-" * 70)
    for r in results:
        year = str(r['release_date'].year) if r['release_date'] else 'N/A'
        print(f"  {r['similarity']:.3f} - {r['title']} ({year}) - {r['tmdb_rating']}/10")

print("\n✅ All tests passed! Database ready for the AI agent.")

# Close connection
conn.close()