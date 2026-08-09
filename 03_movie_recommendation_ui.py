# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# DBTITLE 1,Upgrade Databricks SDK
# MAGIC %pip install --upgrade "databricks-sdk>=0.118.0" --quiet
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# DBTITLE 1,Movie Recommendation UI
# MAGIC %md
# MAGIC # 🎬 AI Movie Night Planner - Interactive UI
# MAGIC
# MAGIC Welcome to your personal AI movie recommendation assistant!
# MAGIC
# MAGIC ## What can I help you find?
# MAGIC
# MAGIC 🔍 **Natural Language Search** - Describe what you're in the mood for
# MAGIC
# MAGIC 🎭 **Genre & Filter Search** - Find movies by genre, rating, and year
# MAGIC
# MAGIC 🎯 **Similar Movies** - Get recommendations based on movies you love
# MAGIC
# MAGIC 👥 **Group Recommendations** - Find the perfect movie for everyone
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC **Quick Start:** Run all cells, then scroll down to use the interactive search tools!

# COMMAND ----------

# DBTITLE 1,Setup: Imports & Connection
# Import all required libraries
import psycopg2
from psycopg2.extras import RealDictCursor
from databricks.sdk import WorkspaceClient
import requests
import json
from typing import List, Dict, Optional, Tuple
from IPython.display import display, HTML, Markdown, clear_output
import ipywidgets as widgets

print("✅ Imports loaded")

# COMMAND ----------

# DBTITLE 1,Connect to Database
# Connect to Lakebase database
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()

print("🔑 Generating database credentials...")
endpoint_name = "projects/movie-night-planner/branches/production/endpoints/primary"
cred = w.postgres.generate_database_credential(endpoint=endpoint_name)
token = cred.token
username = w.current_user.me().user_name

print("🔌 Connecting to database...")
conn = psycopg2.connect(
    host="ep-steep-glitter-d84ausgo.database.us-east-2.cloud.databricks.com",
    port=5432,
    database="databricks_postgres",
    user=username,
    password=token,
    sslmode='require'
)

cursor = conn.cursor()
cursor.execute("SET search_path TO movie_night, public")
conn.commit()
cursor.close()

print("✅ Database connected!")

# COMMAND ----------

# DBTITLE 1,Load Embedding Function
# Setup embedding function
workspace_url = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiUrl().get()
api_token = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()

def generate_embedding(text: str) -> Optional[List[float]]:
    """Generate 1024-dim embedding using Databricks GTE-large."""
    try:
        url = f"{workspace_url}/serving-endpoints/databricks-gte-large-en/invocations"
        response = requests.post(
            url,
            headers={"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"},
            json={"input": [text]}
        )
        if response.status_code == 200:
            return response.json().get('data', [{}])[0].get('embedding', [])
        return None
    except:
        return None

print("✅ Embedding function ready")

# COMMAND ----------

# DBTITLE 1,Load Recommendation Functions
# Core recommendation functions

def search_movies_by_query(query: str, limit: int = 10) -> List[Dict]:
    """Natural language movie search."""
    query_embedding = generate_embedding(query)
    if not query_embedding:
        return []
    
    embedding_str = '[' + ','.join(str(x) for x in query_embedding) + ']'
    
    sql = f"""
        SELECT 
            movie_id, title, EXTRACT(YEAR FROM release_date)::int as release_year,
            genres, director, tmdb_rating as rating, overview,
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

def filter_movies(genres=None, min_rating=None, year_range=None, limit=20):
    """Filter movies by metadata."""
    conditions = []
    params = []
    
    if genres:
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
        SELECT movie_id, title, EXTRACT(YEAR FROM release_date)::int as release_year,
               genres, director, tmdb_rating as rating, overview
        FROM movies
        WHERE {where_clause}
        ORDER BY tmdb_rating DESC
        LIMIT %s
    """
    params.append(limit)
    
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(sql, params)
    results = cursor.fetchall()
    cursor.close()
    return [dict(row) for row in results]

def get_similar_movies(movie_title: str, limit: int = 5):
    """Find similar movies."""
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        "SELECT movie_id, title, content_embedding FROM movies WHERE LOWER(title) LIKE LOWER(%s) AND content_embedding IS NOT NULL LIMIT 1",
        (f"%{movie_title}%",)
    )
    movie = cursor.fetchone()
    cursor.close()
    
    if not movie:
        return []
    
    embedding_str = str(movie['content_embedding'])
    
    sql = f"""
        SELECT movie_id, title, EXTRACT(YEAR FROM release_date)::int as release_year,
               genres, director, tmdb_rating as rating, overview,
               (1 - (content_embedding <=> %s::vector)) as similarity
        FROM movies
        WHERE content_embedding IS NOT NULL AND movie_id != %s
        ORDER BY content_embedding <=> %s::vector
        LIMIT %s
    """
    
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(sql, (embedding_str, movie['movie_id'], embedding_str, limit))
    results = cursor.fetchall()
    cursor.close()
    return [dict(row) for row in results]

def get_genres():
    """Get all genres."""
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT unnest(genres) as genre FROM movies WHERE genres IS NOT NULL ORDER BY genre")
    genres = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return genres

print("✅ All recommendation functions loaded")

# COMMAND ----------

# DBTITLE 1,Display Helpers
# Helper functions for displaying results

def display_movie_card(movie, show_similarity=False):
    """Display a single movie as a nice card."""
    genres_str = ', '.join(movie.get('genres', [])) if isinstance(movie.get('genres'), list) else str(movie.get('genres', 'N/A'))
    
    similarity_badge = ""
    if show_similarity and 'similarity' in movie:
        sim_pct = movie['similarity'] * 100
        similarity_badge = f'<span style="background: #4CAF50; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.85em; margin-left: 10px;">{sim_pct:.1f}% Match</span>'
    
    html = f"""
    <div style="border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin: 10px 0; background: #f9f9f9;">
        <div style="font-size: 1.2em; font-weight: bold; margin-bottom: 8px;">
            🎬 {movie['title']} ({movie.get('release_year', 'N/A')})
            {similarity_badge}
        </div>
        <div style="color: #666; margin-bottom: 5px;">
            <span style="color: #ff9800; font-weight: bold;">⭐ {movie.get('rating', 'N/A')}/10</span>
            <span style="margin-left: 15px;">🎭 {genres_str}</span>
        </div>
        {f'<div style="color: #666; margin-bottom: 8px; font-size: 0.9em;">🎬 Director: {movie.get("director", "N/A")}</div>' if movie.get('director') else ''}
        <div style="color: #444; line-height: 1.5; margin-top: 8px;">{movie.get('overview', 'No description available.')[:200]}{'...' if len(movie.get('overview', '')) > 200 else ''}</div>
    </div>
    """
    display(HTML(html))

def display_results(movies, show_similarity=False):
    """Display a list of movies."""
    if not movies:
        display(HTML('<div style="padding: 20px; text-align: center; color: #999; font-size: 1.1em;">🔍 No movies found. Try adjusting your search criteria.</div>'))
        return
    
    display(HTML(f'<div style="font-size: 1.3em; font-weight: bold; margin: 20px 0 10px 0; color: #333;">🎬 Found {len(movies)} movie{"s" if len(movies) != 1 else ""}:</div>'))
    for movie in movies:
        display_movie_card(movie, show_similarity=show_similarity)

print("✅ Display helpers ready")

# COMMAND ----------

# DBTITLE 1,🔍 Interactive Search: Natural Language
# Natural Language Search Interface
print("🔍 Natural Language Search")
print("=" * 60)
print("Describe what you're looking for in your own words!")
print("Examples:")
print("  - 'funny romantic comedy with happy ending'")
print("  - 'dark thriller with plot twists'")
print("  - 'space adventure with amazing visuals'")
print("  - 'heartwarming family movie'")
print("\n" + "=" * 60)

# Input widget
query_input = widgets.Text(
    value='',
    placeholder='e.g., funny romantic comedy with happy ending',
    description='Query:',
    disabled=False,
    style={'description_width': '80px'},
    layout=widgets.Layout(width='600px')
)

limit_slider = widgets.IntSlider(
    value=5,
    min=1,
    max=20,
    step=1,
    description='Results:',
    style={'description_width': '80px'}
)

search_button = widgets.Button(
    description='🔍 Search Movies',
    button_style='success',
    layout=widgets.Layout(width='200px', height='40px')
)

output = widgets.Output()

def on_search_click(b):
    with output:
        clear_output()
        query = query_input.value.strip()
        if not query:
            display(HTML('<div style="color: #f44336; padding: 10px;">⚠️ Please enter a search query!</div>'))
            return
        
        display(HTML(f'<div style="padding: 10px; background: #e3f2fd; border-radius: 5px; margin: 10px 0;">🔎 Searching for: <strong>{query}</strong></div>'))
        results = search_movies_by_query(query, limit=limit_slider.value)
        display_results(results, show_similarity=True)

search_button.on_click(on_search_click)

display(widgets.VBox([
    query_input,
    limit_slider,
    search_button,
    output
]))

# COMMAND ----------

# DBTITLE 1,🎭 Interactive Search: Genre & Filters
# Genre & Filter Search Interface
print("🎭 Genre & Filter Search")
print("=" * 60)
print("Filter movies by genre, rating, and year range")
print("\n" + "=" * 60)

# Get available genres
available_genres = get_genres()

# Widgets
genre_select = widgets.SelectMultiple(
    options=available_genres,
    value=[],
    description='Genres:',
    disabled=False,
    style={'description_width': '100px'},
    layout=widgets.Layout(width='400px', height='120px')
)

rating_slider = widgets.FloatSlider(
    value=6.0,
    min=0,
    max=10,
    step=0.5,
    description='Min Rating:',
    style={'description_width': '100px'},
    layout=widgets.Layout(width='400px')
)

year_start = widgets.IntText(
    value=2020,
    description='Year From:',
    style={'description_width': '100px'},
    layout=widgets.Layout(width='200px')
)

year_end = widgets.IntText(
    value=2024,
    description='Year To:',
    style={'description_width': '100px'},
    layout=widgets.Layout(width='200px')
)

filter_limit = widgets.IntSlider(
    value=10,
    min=1,
    max=50,
    step=1,
    description='Results:',
    style={'description_width': '100px'},
    layout=widgets.Layout(width='400px')
)

filter_button = widgets.Button(
    description='🎯 Filter Movies',
    button_style='info',
    layout=widgets.Layout(width='200px', height='40px')
)

filter_output = widgets.Output()

def on_filter_click(b):
    with filter_output:
        clear_output()
        
        genres = list(genre_select.value) if genre_select.value else None
        min_rating = rating_slider.value
        year_range = (year_start.value, year_end.value) if year_start.value and year_end.value else None
        
        # Build filter description
        filters_desc = []
        if genres:
            filters_desc.append(f"Genres: {', '.join(genres)}")
        if min_rating:
            filters_desc.append(f"Min Rating: {min_rating}/10")
        if year_range:
            filters_desc.append(f"Years: {year_range[0]}-{year_range[1]}")
        
        filter_text = " | ".join(filters_desc) if filters_desc else "All movies"
        display(HTML(f'<div style="padding: 10px; background: #e8f5e9; border-radius: 5px; margin: 10px 0;">🎯 Filtering: <strong>{filter_text}</strong></div>'))
        
        results = filter_movies(
            genres=genres,
            min_rating=min_rating,
            year_range=year_range,
            limit=filter_limit.value
        )
        display_results(results)

filter_button.on_click(on_filter_click)

display(widgets.VBox([
    genre_select,
    rating_slider,
    widgets.HBox([year_start, year_end]),
    filter_limit,
    filter_button,
    filter_output
]))

# COMMAND ----------

# DBTITLE 1,🎯 Interactive Search: Similar Movies
# Similar Movies Interface
print("🎯 Find Similar Movies")
print("=" * 60)
print("Enter a movie you love, and we'll find similar ones!")
print("\n" + "=" * 60)

# Widgets
movie_title_input = widgets.Text(
    value='',
    placeholder='e.g., The Beekeeper, Inception, Avatar',
    description='Movie Title:',
    disabled=False,
    style={'description_width': '100px'},
    layout=widgets.Layout(width='500px')
)

similar_limit = widgets.IntSlider(
    value=5,
    min=1,
    max=20,
    step=1,
    description='Results:',
    style={'description_width': '100px'},
    layout=widgets.Layout(width='400px')
)

similar_button = widgets.Button(
    description='🔍 Find Similar',
    button_style='warning',
    layout=widgets.Layout(width='200px', height='40px')
)

similar_output = widgets.Output()

def on_similar_click(b):
    with similar_output:
        clear_output()
        title = movie_title_input.value.strip()
        if not title:
            display(HTML('<div style="color: #f44336; padding: 10px;">⚠️ Please enter a movie title!</div>'))
            return
        
        display(HTML(f'<div style="padding: 10px; background: #fff3e0; border-radius: 5px; margin: 10px 0;">🔎 Finding movies similar to: <strong>{title}</strong></div>'))
        results = get_similar_movies(title, limit=similar_limit.value)
        
        if not results:
            display(HTML(f'<div style="color: #f44336; padding: 10px;">❌ Movie "{title}" not found in database. Try a different title or check spelling.</div>'))
        else:
            display_results(results, show_similarity=True)

similar_button.on_click(on_similar_click)

display(widgets.VBox([
    movie_title_input,
    similar_limit,
    similar_button,
    similar_output
]))

# COMMAND ----------

# DBTITLE 1,👥 Interactive Search: Group Recommendations
# Group Recommendations Interface
print("👥 Group Movie Night")
print("=" * 60)
print("Planning a movie night with friends? Enter everyone's preferences!")
print("Add one preference per line.")
print("\nExamples:")
print("  - sci-fi space adventure")
print("  - funny comedy")
print("  - action thriller")
print("\n" + "=" * 60)

# Widgets
preferences_input = widgets.Textarea(
    value='',
    placeholder='Enter preferences (one per line):\nsci-fi space adventure\nfunny comedy\naction',
    description='Preferences:',
    disabled=False,
    style={'description_width': '100px'},
    layout=widgets.Layout(width='500px', height='120px')
)

group_limit = widgets.IntSlider(
    value=5,
    min=1,
    max=20,
    step=1,
    description='Results:',
    style={'description_width': '100px'},
    layout=widgets.Layout(width='400px')
)

group_button = widgets.Button(
    description='🎬 Find Group Movie',
    button_style='danger',
    layout=widgets.Layout(width='200px', height='40px')
)

group_output = widgets.Output()

def on_group_click(b):
    with group_output:
        clear_output()
        prefs_text = preferences_input.value.strip()
        if not prefs_text:
            display(HTML('<div style="color: #f44336; padding: 10px;">⚠️ Please enter at least one preference!</div>'))
            return
        
        # Parse preferences (one per line)
        preferences = [p.strip() for p in prefs_text.split('\n') if p.strip()]
        
        if not preferences:
            display(HTML('<div style="color: #f44336; padding: 10px;">⚠️ Please enter at least one preference!</div>'))
            return
        
        display(HTML(f'<div style="padding: 10px; background: #fce4ec; border-radius: 5px; margin: 10px 0;">👥 Finding movies for {len(preferences)} preference{"s" if len(preferences) > 1 else ""}: <strong>{" + ".join(preferences)}</strong></div>'))
        
        # Generate embeddings and average them
        embeddings = []
        for pref in preferences:
            emb = generate_embedding(pref)
            if emb:
                embeddings.append(emb)
        
        if not embeddings:
            display(HTML('<div style="color: #f44336; padding: 10px;">❌ Failed to process preferences. Please try again.</div>'))
            return
        
        # Average embeddings
        avg_embedding = [sum(dim) / len(embeddings) for dim in zip(*embeddings)]
        embedding_str = '[' + ','.join(str(x) for x in avg_embedding) + ']'
        
        # Search
        sql = f"""
            SELECT movie_id, title, EXTRACT(YEAR FROM release_date)::int as release_year,
                   genres, director, tmdb_rating as rating, overview,
                   (1 - (content_embedding <=> %s::vector)) as similarity
            FROM movies
            WHERE content_embedding IS NOT NULL
            ORDER BY content_embedding <=> %s::vector
            LIMIT %s
        """
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(sql, (embedding_str, embedding_str, group_limit.value))
        results = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        
        display_results(results, show_similarity=True)

group_button.on_click(on_group_click)

display(widgets.VBox([
    preferences_input,
    group_limit,
    group_button,
    group_output
]))

# COMMAND ----------



# COMMAND ----------

# DBTITLE 1,🔥 Demo: Show Popular Recent Movies
# Demo: Show What's Popular Right Now
print("🔥 WHAT'S POPULAR: Top 10 Recent Movies (2020-2024)")
print("=" * 80)
print()

# Get highly-rated recent movies
popular_movies = filter_movies(
    genres=None,  # All genres
    min_rating=7.0,  # High ratings only
    year_range=(2020, 2024),  # Recent movies
    limit=10
)

if popular_movies:
    print(f"Found {len(popular_movies)} highly-rated recent movies:\n")
    display_results(popular_movies)
    
    print("\n" + "="*80)
    print("💡 Want to explore more?")
    print("   • Scroll up to use the Natural Language Search")
    print("   • Try Genre & Filters to customize your search")
    print("   • Find Similar Movies to any of these titles")
else:
    print("No results found. Try adjusting the filters!")