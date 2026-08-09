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
    print("    After restart, continue from cell 2")
    dbutils.library.restartPython()
else:
    print("✅ SDK already up to date, no restart needed")

# COMMAND ----------

# DBTITLE 1,AI Movie Recommendation Agent
# MAGIC %md
# MAGIC # 🎬 AI Movie Recommendation Agent
# MAGIC
# MAGIC This notebook implements a comprehensive AI-powered movie recommendation system using:
# MAGIC
# MAGIC * **Vector Search** - Semantic similarity search using 1024-dimensional embeddings
# MAGIC * **Metadata Filtering** - Genre, rating, year filters for precise recommendations
# MAGIC * **Similar Movies** - Find movies similar to ones you already love
# MAGIC * **Group Recommendations** - Perfect movie for multiple preferences
# MAGIC
# MAGIC ## Features:
# MAGIC
# MAGIC ✅ Natural language queries ("funny romantic comedy with happy ending")
# MAGIC ✅ Advanced filtering (genres, ratings, year ranges)
# MAGIC ✅ Movie similarity search
# MAGIC ✅ Group preference matching
# MAGIC ✅ Detailed movie information with streaming providers
# MAGIC
# MAGIC ---

# COMMAND ----------

# DBTITLE 1,Imports
import psycopg2
from psycopg2.extras import RealDictCursor
from databricks.sdk import WorkspaceClient
import requests
import json
from typing import List, Dict, Optional, Tuple

print("✅ Imports loaded successfully!")

# COMMAND ----------

# DBTITLE 1,Database Connection
# =============================================================================
# LAKEBASE CONNECTION
# =============================================================================

w = WorkspaceClient()

# Generate OAuth token for database
print("🔑 Generating database credentials...")
endpoint_name = "projects/movie-night-planner/branches/production/endpoints/primary"
cred = w.postgres.generate_database_credential(endpoint=endpoint_name)
token = cred.token
username = w.current_user.me().user_name
print(f"   ✅ Got Lakebase JWT token for {username}")

# Connect with psycopg2
print("🔌 Connecting to Lakebase...")
conn = psycopg2.connect(
    host="ep-steep-glitter-d84ausgo.database.us-east-2.cloud.databricks.com",
    port=5432,
    database="databricks_postgres",
    user=username,
    password=token,
    sslmode='require'
)

# Set schema
cursor = conn.cursor()
cursor.execute("SET search_path TO movie_night, public")
conn.commit()
cursor.close()

# Test connection
cursor = conn.cursor(cursor_factory=RealDictCursor)
cursor.execute("SELECT COUNT(*) as count FROM movies")
result = cursor.fetchone()
cursor.close()

print(f"✅ Database connected - Movies in database: {result['count']}")

# COMMAND ----------

# DBTITLE 1,Embedding Function
# =============================================================================
# EMBEDDINGS - Using Databricks Foundation Model APIs
# Model: databricks-gte-large-en (1024 dimensions)
# =============================================================================

# Get workspace credentials
workspace_url = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiUrl().get()
api_token = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()

def generate_embedding(text: str) -> Optional[List[float]]:
    """Generate embedding using Databricks Foundation Model API.
    
    Args:
        text: Text to embed
    
    Returns:
        List of 1024 floats, or None if error
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
            print(f"❌ Embedding API error: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Embedding error: {e}")
        return None

# Test embedding
test_embedding = generate_embedding("A thrilling action movie")
if test_embedding:
    print(f"✅ Embeddings working - Dimension: {len(test_embedding)}")
else:
    print("❌ Embedding test failed")

# COMMAND ----------

# DBTITLE 1,Core Recommendation Functions
# MAGIC %md
# MAGIC ## 🤖 Core Recommendation Functions
# MAGIC
# MAGIC These are the main functions for getting movie recommendations.

# COMMAND ----------

# DBTITLE 1,1. Natural Language Search
def search_movies_by_query(query: str, limit: int = 10) -> List[Dict]:
    """Natural language movie search using vector similarity.
    
    Examples:
        - "funny romantic comedy with happy ending"
        - "dark thriller with plot twists"
        - "space adventure with aliens"
    
    Args:
        query: Natural language description of desired movie
        limit: Maximum number of results
    
    Returns:
        List of movie dicts with similarity scores
    """
    # Generate embedding for query
    query_embedding = generate_embedding(query)
    if not query_embedding:
        print("❌ Failed to generate query embedding")
        return []
    
    # Convert embedding to PostgreSQL array format
    embedding_str = '[' + ','.join(str(x) for x in query_embedding) + ']'
    
    # Vector similarity search using pgvector
    sql = f"""
        SELECT 
            movie_id,
            title,
            EXTRACT(YEAR FROM release_date)::int as release_year,
            genres,
            director,
            tmdb_rating as rating,
            overview,
            (1 - (content_embedding <=> %s::vector)) as similarity
        FROM movies
        WHERE content_embedding IS NOT NULL
        ORDER BY content_embedding <=> %s::vector
        LIMIT %s
    """
    
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(sql, (embedding_str, embedding_str, limit))
    results = cursor.fetchall()
    cursor.close()
    
    return [dict(row) for row in results]

print("✅ search_movies_by_query() ready")

# COMMAND ----------

# DBTITLE 1,2. Metadata Filtering
def filter_movies(
    genres: Optional[List[str]] = None,
    min_rating: Optional[float] = None,
    year_range: Optional[Tuple[int, int]] = None,
    limit: int = 20
) -> List[Dict]:
    """Filter movies by metadata (genres, rating, year).
    
    Examples:
        - filter_movies(genres=['Action', 'Sci-Fi'], min_rating=7.0)
        - filter_movies(year_range=(2020, 2024), min_rating=6.5)
        - filter_movies(genres=['Comedy'], year_range=(2015, 2020))
    
    Args:
        genres: List of genres (movies must have ALL listed genres)
        min_rating: Minimum TMDB rating (0-10)
        year_range: Tuple of (start_year, end_year) inclusive
        limit: Maximum number of results
    
    Returns:
        List of movie dicts
    """
    # Build WHERE clauses
    conditions = []
    params = []
    
    if genres:
        # Check that ALL genres are present (genres is a text[] array)
        for genre in genres:
            conditions.append("%s = ANY(genres)")
            params.append(genre)
    
    if min_rating is not None:
        conditions.append("tmdb_rating >= %s")
        params.append(min_rating)
    
    if year_range:
        conditions.append("EXTRACT(YEAR FROM release_date) BETWEEN %s AND %s")
        params.extend(year_range)
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    sql = f"""
        SELECT 
            movie_id,
            title,
            EXTRACT(YEAR FROM release_date)::int as release_year,
            genres,
            director,
            tmdb_rating as rating,
            overview,
            tmdb_vote_count as vote_count
        FROM movies
        WHERE {where_clause}
        ORDER BY tmdb_rating DESC, tmdb_vote_count DESC
        LIMIT %s
    """
    
    params.append(limit)
    
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(sql, params)
    results = cursor.fetchall()
    cursor.close()
    
    return [dict(row) for row in results]

print("✅ filter_movies() ready")

# COMMAND ----------

# DBTITLE 1,3. Similar Movies
def get_similar_movies(movie_title: str, limit: int = 5) -> List[Dict]:
    """Find movies similar to a given movie title.
    
    Examples:
        - get_similar_movies("The Beekeeper")
        - get_similar_movies("Inception", limit=10)
    
    Args:
        movie_title: Title of the reference movie
        limit: Maximum number of similar movies to return
    
    Returns:
        List of similar movie dicts with similarity scores
    """
    # Find the movie by title (case-insensitive partial match)
    sql = """
        SELECT movie_id, title, content_embedding
        FROM movies
        WHERE LOWER(title) LIKE LOWER(%s)
        AND content_embedding IS NOT NULL
        LIMIT 1
    """
    
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(sql, (f"%{movie_title}%",))
    movie = cursor.fetchone()
    cursor.close()
    
    if not movie:
        print(f"❌ Movie not found: {movie_title}")
        return []
    
    print(f"🎬 Found reference movie: {movie['title']}")
    
    # Convert embedding to PostgreSQL array format
    embedding_str = str(movie['content_embedding'])
    
    # Find similar movies (excluding the reference movie itself)
    sql = f"""
        SELECT 
            movie_id,
            title,
            EXTRACT(YEAR FROM release_date)::int as release_year,
            genres,
            director,
            tmdb_rating as rating,
            overview,
            (1 - (content_embedding <=> %s::vector)) as similarity
        FROM movies
        WHERE content_embedding IS NOT NULL
        AND movie_id != %s
        ORDER BY content_embedding <=> %s::vector
        LIMIT %s
    """
    
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(sql, (embedding_str, movie['movie_id'], embedding_str, limit))
    results = cursor.fetchall()
    cursor.close()
    
    return [dict(row) for row in results]

print("✅ get_similar_movies() ready")

# COMMAND ----------

# DBTITLE 1,4. Group Recommendations
def recommend_for_group(preferences: List[str], limit: int = 10) -> List[Dict]:
    """Find movies matching multiple user preferences (group recommendations).
    
    This generates an embedding for each preference, averages them, and finds
    movies closest to that "consensus" embedding.
    
    Examples:
        - recommend_for_group(["sci-fi space adventure", "comedy", "action"])
        - recommend_for_group(["romantic drama", "historical period piece"])
    
    Args:
        preferences: List of natural language preference descriptions
        limit: Maximum number of results
    
    Returns:
        List of movie dicts with similarity scores to group consensus
    """
    if not preferences:
        print("❌ No preferences provided")
        return []
    
    print(f"👥 Processing {len(preferences)} preferences...")
    
    # Generate embeddings for each preference
    embeddings = []
    for i, pref in enumerate(preferences, 1):
        emb = generate_embedding(pref)
        if emb:
            embeddings.append(emb)
            print(f"   [{i}/{len(preferences)}] Generated: {pref}")
        else:
            print(f"   ❌ Failed: {pref}")
    
    if not embeddings:
        print("❌ Failed to generate any embeddings")
        return []
    
    # Average the embeddings (consensus)
    avg_embedding = [sum(dim) / len(embeddings) for dim in zip(*embeddings)]
    
    # Convert to PostgreSQL array format
    embedding_str = '[' + ','.join(str(x) for x in avg_embedding) + ']'
    
    # Find movies closest to consensus
    sql = f"""
        SELECT 
            movie_id,
            title,
            EXTRACT(YEAR FROM release_date)::int as release_year,
            genres,
            director,
            tmdb_rating as rating,
            overview,
            (1 - (content_embedding <=> %s::vector)) as similarity
        FROM movies
        WHERE content_embedding IS NOT NULL
        ORDER BY content_embedding <=> %s::vector
        LIMIT %s
    """
    
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(sql, (embedding_str, embedding_str, limit))
    results = cursor.fetchall()
    cursor.close()
    
    print(f"✅ Found {len(results)} movies matching group preferences")
    return [dict(row) for row in results]

print("✅ recommend_for_group() ready")

# COMMAND ----------

# DBTITLE 1,Helper Functions
# MAGIC %md
# MAGIC ## 🛠️ Helper Functions
# MAGIC
# MAGIC Utility functions for movie information and exploration.

# COMMAND ----------

# DBTITLE 1,Get Movie Details
def get_movie_details(movie_id: int) -> Optional[Dict]:
    """Get full details for a movie by ID.
    
    Args:
        movie_id: TMDB movie ID
    
    Returns:
        Dict with all movie info including streaming providers, or None if not found
    """
    sql = """
        SELECT 
            movie_id,
            title,
            EXTRACT(YEAR FROM release_date)::int as release_year,
            genres,
            director,
            tmdb_rating as rating,
            tmdb_vote_count as vote_count,
            runtime,
            overview,
            tagline,
            keywords,
            cast_names,
            streaming_providers,
            poster_path,
            backdrop_path
        FROM movies
        WHERE movie_id = %s
    """
    
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(sql, (movie_id,))
    movie = cursor.fetchone()
    cursor.close()
    
    return dict(movie) if movie else None

print("✅ get_movie_details() ready")

# COMMAND ----------

# DBTITLE 1,Get All Genres
def get_genres() -> List[str]:
    """Get list of all unique genres in the database.
    
    Returns:
        Sorted list of genre names
    """
    sql = """
        SELECT DISTINCT unnest(genres) as genre
        FROM movies
        WHERE genres IS NOT NULL
        ORDER BY genre
    """
    
    cursor = conn.cursor()
    cursor.execute(sql)
    genres = [row[0] for row in cursor.fetchall()]
    cursor.close()
    
    return genres

print("✅ get_genres() ready")

# COMMAND ----------

# DBTITLE 1,Find Movie by Title
def get_movie_by_title(title: str) -> Optional[Dict]:
    """Find a movie by exact or fuzzy title match.
    
    Args:
        title: Full or partial movie title (case-insensitive)
    
    Returns:
        Movie dict if found, None otherwise
    """
    # Try exact match first
    sql = """
        SELECT 
            movie_id,
            title,
            EXTRACT(YEAR FROM release_date)::int as release_year,
            genres,
            director,
            tmdb_rating as rating,
            overview
        FROM movies
        WHERE LOWER(title) = LOWER(%s)
        LIMIT 1
    """
    
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(sql, (title,))
    movie = cursor.fetchone()
    
    # If no exact match, try partial match
    if not movie:
        sql = """
            SELECT 
                movie_id,
                title,
                EXTRACT(YEAR FROM release_date)::int as release_year,
                genres,
                director,
                tmdb_rating as rating,
                overview
            FROM movies
            WHERE LOWER(title) LIKE LOWER(%s)
            ORDER BY tmdb_rating DESC
            LIMIT 1
        """
        cursor.execute(sql, (f"%{title}%",))
        movie = cursor.fetchone()
    
    cursor.close()
    
    return dict(movie) if movie else None

print("✅ get_movie_by_title() ready")

# COMMAND ----------

# DBTITLE 1,Tests & Demos
# MAGIC %md
# MAGIC ## 🧪 Tests & Demos
# MAGIC
# MAGIC Examples showing all recommendation capabilities.

# COMMAND ----------

# DBTITLE 1,Test 1: Natural Language Search
# Test 1: Natural Language Search
print("🔍 Test 1: Natural Language Search")
print("=" * 70)

query = "funny romantic comedy with happy ending"
print(f"Query: '{query}'\n")

results = search_movies_by_query(query, limit=5)

print(f"\n🎬 Found {len(results)} movies:\n")
for movie in results:
    sim_pct = movie['similarity'] * 100
    print(f"  {sim_pct:5.1f}% - {movie['title']} ({movie['release_year']})")
    print(f"         {movie['genres']} - {movie['rating']}/10")
    print(f"         {movie['overview'][:80]}...\n")

# COMMAND ----------

# DBTITLE 1,Test 2: Genre Filtering
# Test 2: Genre & Metadata Filtering
print("🎬 Test 2: Genre & Metadata Filtering")
print("=" * 70)

print("Filter: Action movies from 2020-2024 with rating > 7.0\n")

results = filter_movies(
    genres=['Action'],
    min_rating=7.0,
    year_range=(2020, 2024),
    limit=10
)

print(f"\n🎬 Found {len(results)} movies:\n")
for movie in results:
    print(f"  ⭐ {movie['rating']}/10 - {movie['title']} ({movie['release_year']})")
    print(f"     {movie['genres']}")
    print(f"     Director: {movie['director']}\n")

# COMMAND ----------

# DBTITLE 1,Test 3: Similar Movies
# Test 3: Similar Movies
print("🎬 Test 3: Similar Movies")
print("=" * 70)

reference = "The Beekeeper"
print(f"Find movies similar to: {reference}\n")

results = get_similar_movies(reference, limit=5)

if results:
    print(f"\n🎬 Found {len(results)} similar movies:\n")
    for movie in results:
        sim_pct = movie['similarity'] * 100
        print(f"  {sim_pct:5.1f}% - {movie['title']} ({movie['release_year']}) - {movie['rating']}/10")
        print(f"         {movie['genres']}")
        print(f"         {movie['overview'][:80]}...\n")
else:
    print("\n❌ No similar movies found or reference movie not in database")

# COMMAND ----------

# DBTITLE 1,Test 4: Group Recommendations
# Test 4: Group Recommendations
print("👥 Test 4: Group Recommendations")
print("=" * 70)

preferences = [
    "sci-fi space adventure",
    "comedy",
    "action"
]

print("Group preferences:")
for i, pref in enumerate(preferences, 1):
    print(f"  {i}. {pref}")

print()

results = recommend_for_group(preferences, limit=5)

print(f"\n🎬 Top {len(results)} movies for the group:\n")
for i, movie in enumerate(results, 1):
    sim_pct = movie['similarity'] * 100
    print(f"  {i}. {movie['title']} ({movie['release_year']}) - {movie['rating']}/10")
    print(f"     Match: {sim_pct:.1f}% | {movie['genres']}")
    print(f"     {movie['overview'][:100]}...\n")

# COMMAND ----------

# DBTITLE 1,Bonus: Helper Functions Demo
# Bonus: Helper Functions Demo
print("🛠️ Bonus: Helper Functions")
print("=" * 70)

# Get all available genres
print("\n1. Available Genres:")
genres = get_genres()
print(f"   {len(genres)} genres: {', '.join(genres[:10])}...\n")

# Find movie by title
print("2. Find Movie by Title:")
movie = get_movie_by_title("Beekeeper")
if movie:
    print(f"   Found: {movie['title']} ({movie['release_year']})")
    print(f"   {movie['genres']} - {movie['rating']}/10\n")

# Get full movie details
print("3. Get Full Movie Details:")
if movie:
    details = get_movie_details(movie['movie_id'])
    if details:
        print(f"   Title: {details['title']}")
        print(f"   Runtime: {details['runtime']} min")
        print(f"   Tagline: {details['tagline']}")
        print(f"   Keywords: {details['keywords'][:50] if details['keywords'] else 'N/A'}...")
        print(f"   Cast: {details['cast_names'][:50] if details['cast_names'] else 'N/A'}...")
        if details['streaming_providers']:
            print(f"   Streaming: {details['streaming_providers']}")

print("\n" + "=" * 70)
print("✅ All functions working! Agent ready for use.")