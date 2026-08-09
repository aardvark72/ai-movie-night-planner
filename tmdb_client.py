"""
TMDB (The Movie Database) API Client.

Free tier: 40 requests per 10 seconds
Docs: https://developer.themoviedb.org/docs
"""

import time
from typing import List, Optional

import requests


class TMDBClient:
    """Client for The Movie Database (TMDB) API."""
    
    def __init__(self, api_key: str, rate_limit: int = 40):
        """Initialize TMDB client.
        
        Args:
            api_key: TMDB API key
            rate_limit: Max requests per 10 seconds (default 40 for free tier)
        """
        self.api_key = api_key
        self.base_url = "https://api.themoviedb.org/3"
        self.rate_limit = rate_limit
        self._request_times = []
    
    def _rate_limit_check(self):
        """Ensure we don't exceed rate limits."""
        now = time.time()
        # Remove requests older than 10 seconds
        self._request_times = [t for t in self._request_times if now - t < 10]
        
        if len(self._request_times) >= self.rate_limit:
            # Wait until the oldest request is 10 seconds old
            sleep_time = 10 - (now - self._request_times[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
                self._request_times = self._request_times[1:]
        
        self._request_times.append(now)
    
    def _request(self, endpoint: str, params: dict = None) -> dict:
        """Make a rate-limited request to TMDB API."""
        self._rate_limit_check()
        
        url = f"{self.base_url}{endpoint}"
        params = params or {}
        params['api_key'] = self.api_key
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    
    def search_movies(self, query: str, year: Optional[int] = None, page: int = 1) -> dict:
        """Search movies by title.
        
        Args:
            query: Movie title to search for
            year: Filter by release year (optional)
            page: Page number (default 1)
        
        Returns:
            dict with 'results' list and pagination info
        """
        params = {'query': query, 'page': page}
        if year:
            params['year'] = year
        
        return self._request('/search/movie', params)
    
    def get_movie_details(self, movie_id: int) -> dict:
        """Get detailed movie information.
        
        Includes: genres, runtime, cast, crew, keywords, videos
        """
        return self._request(
            f'/movie/{movie_id}',
            params={
                'append_to_response': 'credits,keywords,videos,watch/providers,reviews'
            }
        )
    
    def get_popular_movies(self, page: int = 1) -> dict:
        """Get popular movies (paginated)."""
        return self._request('/movie/popular', {'page': page})
    
    def get_top_rated_movies(self, page: int = 1) -> dict:
        """Get top-rated movies (paginated)."""
        return self._request('/movie/top_rated', {'page': page})
    
    def discover_movies(
        self,
        genres: Optional[List[int]] = None,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        min_rating: Optional[float] = None,
        max_runtime: Optional[int] = None,
        page: int = 1
    ) -> dict:
        """Advanced movie discovery with filters.
        
        Args:
            genres: List of genre IDs (use get_genres() to get mapping)
            year_from: Minimum release year
            year_to: Maximum release year
            min_rating: Minimum TMDB rating (0-10)
            max_runtime: Maximum runtime in minutes
            page: Page number
        
        Returns:
            dict with 'results' list and pagination info
        """
        params = {'page': page, 'sort_by': 'popularity.desc'}
        
        if genres:
            params['with_genres'] = ','.join(str(g) for g in genres)
        if year_from:
            params['primary_release_date.gte'] = f"{year_from}-01-01"
        if year_to:
            params['primary_release_date.lte'] = f"{year_to}-12-31"
        if min_rating:
            params['vote_average.gte'] = min_rating
        if max_runtime:
            params['with_runtime.lte'] = max_runtime
        
        return self._request('/discover/movie', params)
    
    def get_genres(self) -> dict:
        """Get list of official TMDB genres.
        
        Returns:
            dict with 'genres' list: [{'id': 28, 'name': 'Action'}, ...]
        """
        return self._request('/genre/movie/list')
    
    def get_movie_reviews(self, movie_id: int, page: int = 1) -> dict:
        """Get user reviews for a movie."""
        return self._request(f'/movie/{movie_id}/reviews', {'page': page})
    
    def get_streaming_providers(self, movie_id: int, region: str = 'US') -> dict:
        """Get streaming availability by region.
        
        Args:
            movie_id: TMDB movie ID
            region: ISO 3166-1 country code (default 'US')
        
        Returns:
            dict with 'results' key containing provider info by region
        """
        return self._request(f'/movie/{movie_id}/watch/providers')
