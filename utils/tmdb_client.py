"""
TMDB API Client

Wrapper for The Movie Database (TMDB) API v3.

API Documentation: https://developers.themoviedb.org/3
Rate Limits: 40 requests per 10 seconds (free tier)
"""

import requests
import time
from typing import Dict, List, Optional, Any


class TMDBClient:
    """
    Client for interacting with TMDB API.
    
    Usage:
        client = TMDBClient(api_key="your_api_key")
        movies = client.discover_movies(year=2023, min_rating=7.0)
        details = client.get_movie_details(movie_id=550)
    """
    
    BASE_URL = "https://api.themoviedb.org/3"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
    
    def _request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a request to TMDB API with rate limiting."""
        # TODO: Implement rate limiting (40 req/10s)
        # TODO: Add error handling and retries
        pass
    
    # ========================================================================
    # Discover & Search
    # ========================================================================
    
    def discover_movies(
        self,
        year: Optional[int] = None,
        min_rating: Optional[float] = None,
        genres: Optional[List[str]] = None,
        page: int = 1
    ) -> Dict[str, Any]:
        """Discover movies with filters."""
        # TODO: Implement discover endpoint
        pass
    
    # ========================================================================
    # Movie Details
    # ========================================================================
    
    def get_movie_details(self, movie_id: int) -> Dict[str, Any]:
        """Get full movie details."""
        # TODO: Implement /movie/{id}
        pass
    
    def get_movie_credits(self, movie_id: int) -> Dict[str, Any]:
        """Get cast and crew."""
        # TODO: Implement /movie/{id}/credits
        pass
    
    def get_movie_keywords(self, movie_id: int) -> List[str]:
        """Get movie keywords/tags."""
        # TODO: Implement /movie/{id}/keywords
        pass
    
    def get_movie_videos(self, movie_id: int) -> List[Dict[str, Any]]:
        """Get trailers and videos."""
        # TODO: Implement /movie/{id}/videos
        pass
    
    def get_watch_providers(self, movie_id: int, region: str = "US") -> Dict[str, Any]:
        """Get streaming availability."""
        # TODO: Implement /movie/{id}/watch/providers
        pass


# TODO: Add batch processing utilities for fetching multiple movies efficiently