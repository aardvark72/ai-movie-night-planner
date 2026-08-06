"""
AI Agent Tools

Defines the 6 tools available to the movie recommendation agent:
- 3 READ tools: search_movies, get_group_preferences, explain_recommendation
- 3 WRITE tools: add_to_watchlist, record_rating, compare_movies
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


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
# Tool Implementations
# ============================================================================

def search_movies(input: SearchMoviesInput) -> Dict[str, Any]:
    """
    Semantic search for movies matching a natural language query.
    
    Steps:
    1. Generate embedding for query
    2. Query Lakebase with vector similarity + filters
    3. Exclude movies already watched by group
    4. Rank by group preferences
    5. Return top N with explanations
    """
    # TODO: Implement semantic search
    pass


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