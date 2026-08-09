"""
AI Agent Tools

Defines the 6 tools available to the movie recommendation agent:
- 3 READ tools: search_movies, get_group_preferences, explain_recommendation
- 3 WRITE tools: add_to_watchlist, record_rating, compare_movies
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import psycopg2


# ============================================================================
# Tool Schemas (Pydantic models for input validation)
# ============================================================================

class SearchMoviesInput(BaseModel):
    """Input for search_movies tool."""
    query: str = Field(description="Natural language movie search query")
    group_id: Optional[int] = Field(default=None, description="Group ID for preference ranking")
    max_runtime: Optional[int] = Field(default=None, description="Max runtime in minutes")
    min_rating: Optional[float] = Field(default=None, description="Minimum TMDB rating")
    limit: int = Field(default=10, description="Max number of results")


class AddToWatchlistInput(BaseModel):
    """Input for add_to_watchlist tool."""
    group_id: int = Field(description="Group ID")
    movie_id: int = Field(description="Movie ID to add")
    added_by_user_id: int = Field(description="User ID who added it")
    notes: Optional[str] = Field(default=None, description="Optional notes")
    priority: int = Field(default=5, description="Priority (1-10)")


class RecordRatingInput(BaseModel):
    """Input for record_rating tool."""
    user_id: int = Field(description="User ID")
    movie_id: int = Field(description="Movie ID")
    rating: float = Field(description="Rating (0.5-5.0 stars)", ge=0.5, le=5.0)
    review_text: Optional[str] = Field(default=None, description="Optional review")
    watched_date: Optional[str] = Field(default=None, description="Date watched (YYYY-MM-DD)")


# ============================================================================
# Helper Functions  
# ============================================================================

def _get_db_connection():
    """Get database connection using environment variables (for Databricks Apps)."""
    import os
    
    # In Databricks Apps, connection URL is set directly in environment
    connection_url = os.environ.get('LAKEBASE_CONNECTION_URL')
    
    if not connection_url:
        raise ValueError("LAKEBASE_CONNECTION_URL environment variable not set")
    
    # Connect directly with the URL (no base64 decoding needed)
    conn = psycopg2.connect(connection_url)
    cursor = conn.cursor()
    cursor.execute("SET search_path TO movie_night, public")
    cursor.close()
    return conn

def _generate_embedding(text: str) -> List[float]:
    """Generate embedding using Databricks Foundation Model API."""
    import os
    try:
        # Try to get from environment variables first (Databricks Apps)
        host = os.environ.get('DATABRICKS_HOST')
        token = os.environ.get('DATABRICKS_TOKEN')
        
        # Fallback to WorkspaceClient if env vars not available
        if not host or not token:
            from databricks.sdk import WorkspaceClient
            w = WorkspaceClient()
            host = w.config.host
            token = w.config.token
        
        url = f"{host}/serving-endpoints/databricks-gte-large-en/invocations"
        response = requests.post(
            url,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"input": [text]}
        )
        if response.status_code == 200:
            return response.json().get('data', [{}])[0].get('embedding', [])
        return None
    except Exception as e:
        print(f"Embedding error: {e}")
        return None

# ============================================================================
# Tool Implementations
# ============================================================================

def search_movies(input: SearchMoviesInput) -> Dict[str, Any]:
    """
    Semantic search for movies matching a natural language query.
    """
    try:
        query_embedding = _generate_embedding(input.query)
        if not query_embedding:
            return {"error": "Failed to generate embedding"}
        
        conn = _get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        sql = """
            SELECT m.movie_id, m.title, m.release_date, m.runtime, m.overview,
                   m.genres, m.director, m.cast_names, m.tmdb_rating,
                   1 - (e.content_embedding <=> %s::vector) as similarity_score
            FROM movies m
            JOIN movie_embeddings e ON m.movie_id = e.movie_id
            WHERE e.content_embedding IS NOT NULL
        """
        params = [query_embedding]
        
        if input.max_runtime:
            sql += " AND m.runtime <= %s"
            params.append(input.max_runtime)
        if input.min_rating:
            sql += " AND m.tmdb_rating >= %s"
            params.append(input.min_rating)
        if input.group_id:
            sql += " AND m.movie_id NOT IN (SELECT r.movie_id FROM ratings r JOIN group_members gm ON r.user_id = gm.user_id WHERE gm.group_id = %s)"
            params.append(input.group_id)
        
        sql += " ORDER BY e.content_embedding <=> %s::vector LIMIT %s"
        params.extend([query_embedding, input.limit])
        
        cursor.execute(sql, params)
        results = [{**dict(row), 'year': row['release_date'].year if row['release_date'] else None} for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        
        return {"success": True, "query": input.query, "count": len(results), "movies": results}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_group_preferences(group_id: int) -> Dict[str, Any]:
    """
    Analyze a group's viewing history and preferences.
    
    Returns:
    - Top genres
    - Favorite movies
    - Disliked genres
    - Average runtime preference
    - Streaming services
    """
    # TODO: Implement preference analysis
    pass


def add_to_watchlist(input: AddToWatchlistInput) -> Dict[str, Any]:
    """
    Add a movie to the group's watchlist.
    
    Returns success/failure and watchlist_id.
    """
    # TODO: Implement database INSERT
    pass


def record_rating(input: RecordRatingInput) -> Dict[str, Any]:
    """
    Record a user's rating after watching a movie.
    
    Also marks the movie as watched in the group watchlist.
    """
    # TODO: Implement database INSERT/UPDATE
    pass


def explain_recommendation(movie_id: int, group_id: int, user_query: str) -> Dict[str, Any]:
    """
    Provide detailed explanation of why a movie was recommended.
    
    Explains:
    - Semantic match to query
    - Group preference fit
    - Practical considerations (streaming, runtime)
    - Ratings and reviews
    - What it avoids (disliked genres)
    """
    # TODO: Implement explanation generation
    pass


def compare_movies(movie_ids: List[int], group_id: int) -> Dict[str, Any]:
    """
    Compare multiple movies for group decision-making.
    
    Returns pros/cons and recommendation.
    """
    # TODO: Implement comparison logic
    pass


def get_watchlist_items(group_id: int) -> List[Dict[str, Any]]:
    """
    Get all watchlist items for a group.
    
    Args:
        group_id: The group ID
        
    Returns:
        List of watchlist items with movie details
    """
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = """
            SELECT 
                w.id,
                w.movie_id,
                m.title,
                m.release_year,
                m.tmdb_rating,
                m.runtime_minutes,
                w.notes,
                w.priority,
                w.added_at
            FROM watchlist_items w
            JOIN movies m ON w.movie_id = m.id
            WHERE w.group_id = %s
            ORDER BY w.priority DESC, w.added_at DESC
        """
        
        cursor.execute(query, (group_id,))
        items = cursor.fetchall()
        
        return [{
            "id": item[0],
            "movie_id": item[1],
            "title": item[2],
            "release_year": item[3],
            "tmdb_rating": float(item[4]) if item[4] else None,
            "runtime_minutes": item[5],
            "notes": item[6],
            "priority": item[7],
            "added_at": str(item[8])
        } for item in items]
        
    except Exception as e:
        return {"error": str(e)}
    finally:
        cursor.close()
        conn.close()


# ============================================================================
# Tool Registry (for LangChain/Agent Framework)
# ============================================================================

TOOLS = [
    {
        "name": "search_movies",
        "description": "Search for movies using natural language. Returns semantic matches ranked by group preferences.",
        "function": search_movies,
        "schema": SearchMoviesInput
    },
    {
        "name": "get_group_preferences",
        "description": "Analyze a group's viewing history and preferences.",
        "function": get_group_preferences
    },
    {
        "name": "add_to_watchlist",
        "description": "Add a movie to a group's watchlist.",
        "function": add_to_watchlist,
        "schema": AddToWatchlistInput
    },
    {
        "name": "record_rating",
        "description": "Record a user's rating after watching a movie.",
        "function": record_rating,
        "schema": RecordRatingInput
    },
    {
        "name": "explain_recommendation",
        "description": "Explain why a movie was recommended.",
        "function": explain_recommendation
    },
    {
        "name": "compare_movies",
        "description": "Compare multiple movies for group decision-making.",
        "function": compare_movies
    }
]