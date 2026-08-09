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
        if params is None:
            params = {}
        
        params['api_key'] = self.api_key
        
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            # Rate limiting: ~0.25s between requests = 40 req/10s
            time.sleep(0.26)
            
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                # Rate limit hit - wait longer
                time.sleep(10)
                return self._request(endpoint, params)
            else:
                print(f"HTTP error for {endpoint}: {e}")
                return {}
        except Exception as e:
            print(f"Error requesting {endpoint}: {e}")
            return {}
    
    # ========================================================================
    # Discover & Search
    # ========================================================================
    
    def discover_movies(
        self,
        year: Optional[int] = None,
        min_rating: Optional[float] = None,
        min_votes: Optional[int] = None,
        genres: Optional[List[str]] = None,
        page: int = 1
    ) -> Dict[str, Any]:
        """Discover movies with filters.
        
        Args:
            year: Release year
            min_rating: Minimum TMDB rating (0-10)
            min_votes: Minimum vote count
            genres: List of genre IDs
            page: Page number (max 500 results per page)
        
        Returns:
            Dict with 'results' list and pagination info
        """
        params = {
            'sort_by': 'popularity.desc',
            'include_adult': 'false',
            'include_video': 'false',
            'language': 'en-US',
            'page': page
        }
        
        if year:
            params['primary_release_year'] = year
        
        if min_rating:
            params['vote_average.gte'] = min_rating
        
        if min_votes:
            params['vote_count.gte'] = min_votes
        
        if genres:
            params['with_genres'] = ','.join(map(str, genres))
        
        return self._request('/discover/movie', params)
    
    # ========================================================================
    # Movie Details
    # ========================================================================
    
    def get_movie_details(self, movie_id: int) -> Dict[str, Any]:
        """Get full movie details including genres, runtime, tagline, etc.
        
        Returns:
            Dict with all movie metadata from TMDB
        """
        return self._request(f'/movie/{movie_id}', {'language': 'en-US'})
    
    def get_movie_credits(self, movie_id: int) -> Dict[str, Any]:
        """Get cast and crew.
        
        Returns:
            Dict with 'cast' and 'crew' arrays
        """
        return self._request(f'/movie/{movie_id}/credits')
    
    def get_movie_keywords(self, movie_id: int) -> List[str]:
        """Get movie keywords/tags.
        
        Returns:
            List of keyword strings
        """
        data = self._request(f'/movie/{movie_id}/keywords')
        return [kw['name'] for kw in data.get('keywords', [])]
    
    def get_movie_videos(self, movie_id: int) -> List[Dict[str, Any]]:
        """Get trailers and videos.
        
        Returns:
            List of video dicts with 'type', 'key', 'site' fields
        """
        data = self._request(f'/movie/{movie_id}/videos', {'language': 'en-US'})
        return data.get('results', [])
    
    def get_watch_providers(self, movie_id: int, region: str = "US") -> Dict[str, Any]:
        """Get streaming availability for a specific region.
        
        Args:
            movie_id: TMDB movie ID
            region: Two-letter country code (default: US)
        
        Returns:
            Dict with 'flatrate' (streaming), 'rent', 'buy' providers
        """
        data = self._request(f'/movie/{movie_id}/watch/providers')
        results = data.get('results', {})
        return results.get(region, {})
    
    def get_content_rating(self, movie_id: int, region: str = "US") -> Optional[str]:
        """Get content rating (G, PG, PG-13, R, etc.) for a region.
        
        Args:
            movie_id: TMDB movie ID
            region: Two-letter country code (default: US)
        
        Returns:
            Rating string (e.g., 'PG-13') or None
        """
        data = self._request(f'/movie/{movie_id}/release_dates')
        results = data.get('results', [])
        
        for result in results:
            if result.get('iso_3166_1') == region:
                release_dates = result.get('release_dates', [])
                for rd in release_dates:
                    cert = rd.get('certification')
                    if cert:
                        return cert
        return None
    
    def get_movie_full(self, movie_id: int) -> Dict[str, Any]:
        """Get all movie data in one consolidated dict.
        
        This fetches details, credits, keywords, videos, providers, and ratings
        in separate API calls and combines them into a single dict.
        
        Args:
            movie_id: TMDB movie ID
        
        Returns:
            Combined dict with all movie data
        """
        details = self.get_movie_details(movie_id)
        if not details:
            return {}
        
        credits = self.get_movie_credits(movie_id)
        keywords = self.get_movie_keywords(movie_id)
        videos = self.get_movie_videos(movie_id)
        providers = self.get_watch_providers(movie_id)
        content_rating = self.get_content_rating(movie_id)
        
        # Find director
        director = None
        for crew_member in credits.get('crew', []):
            if crew_member.get('job') == 'Director':
                director = crew_member.get('name')
                break
        
        # Get top 10 cast
        cast_names = [actor.get('name') for actor in credits.get('cast', [])[:10]]
        
        # Get YouTube trailer
        trailer_url = None
        for video in videos:
            if video.get('type') == 'Trailer' and video.get('site') == 'YouTube':
                trailer_url = f"https://www.youtube.com/watch?v={video.get('key')}"
                break
        
        # Combine all data
        return {
            'tmdb_id': details.get('id'),
            'title': details.get('title'),
            'original_title': details.get('original_title'),
            'release_date': details.get('release_date'),
            'runtime': details.get('runtime'),
            'overview': details.get('overview'),
            'tagline': details.get('tagline'),
            'genres': [g['name'] for g in details.get('genres', [])],
            'keywords': keywords,
            'director': director,
            'cast_names': cast_names,
            'tmdb_rating': details.get('vote_average'),
            'tmdb_vote_count': details.get('vote_count'),
            'popularity': details.get('popularity'),
            'content_rating': content_rating,
            'poster_path': details.get('poster_path'),
            'backdrop_path': details.get('backdrop_path'),
            'trailer_url': trailer_url,
            'streaming_providers': providers,
            'raw_data': details
        }