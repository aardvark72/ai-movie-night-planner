"""
Movie Card Component

Displays movie information in a card format with poster, details, and actions.
"""

import streamlit as st
from typing import Dict, Any, Optional


def render_movie_card(
    movie: Dict[str, Any], 
    show_actions: bool = True,
    similarity_score: Optional[float] = None
):
    """
    Render a movie card with poster, details, and action buttons.
    
    Args:
        movie: Movie data dict with title, genres, rating, etc.
        show_actions: Whether to show action buttons (Add to Watchlist, Rate)
        similarity_score: Optional similarity score for search results
    """
    
    # Extract movie data
    movie_id = movie.get("id") or movie.get("movie_id")
    title = movie.get("title", "Unknown Title")
    year = movie.get("release_year", "")
    runtime = movie.get("runtime_minutes", 0)
    rating = movie.get("tmdb_rating", 0)
    genres = movie.get("genres", [])
    overview = movie.get("overview", "No overview available.")
    poster_url = movie.get("poster_url")
    cast = movie.get("cast_names", []) if isinstance(movie.get("cast_names"), list) else []
    
    # Create card container
    with st.container():
        col1, col2 = st.columns([1, 3])
        
        # Left column: Poster
        with col1:
            if poster_url and poster_url.startswith("http"):
                st.image(poster_url, use_column_width=True)
            else:
                st.image("https://via.placeholder.com/300x450?text=No+Poster", 
                        use_column_width=True)
        
        # Right column: Details
        with col2:
            # Title and year
            st.markdown(f"### {title}")
            if year:
                st.caption(f"📅 {year}")
            
            # Similarity score (if search result)
            if similarity_score is not None:
                match_percent = int(similarity_score * 100)
                st.progress(similarity_score, text=f"🎯 {match_percent}% match")
            
            # Rating and runtime
            col_a, col_b = st.columns(2)
            with col_a:
                stars = "⭐" * int(rating / 2)
                st.markdown(f"{stars} **{rating:.1f}/10**")
            with col_b:
                if runtime:
                    hours = runtime // 60
                    mins = runtime % 60
                    st.markdown(f"⏱️ {hours}h {mins}m")
            
            # Genres
            if genres:
                genre_badges = " · ".join(genres[:4])  # Limit to 4 genres
                st.markdown(f"🎬 {genre_badges}")
            
            # Cast (top 3)
            if cast:
                cast_str = ", ".join(cast[:3])
                st.caption(f"🎭 {cast_str}")
            
            # Overview
            with st.expander("📖 Overview"):
                st.write(overview)
            
            # Action buttons
            if show_actions:
                col_x, col_y, col_z = st.columns(3)
                
                with col_x:
                    if st.button("➕ Watchlist", key=f"add_{movie_id}", use_container_width=True):
                        st.session_state.action_movie_id = movie_id
                        st.session_state.action_type = "add_watchlist"
                        st.rerun()
                
                with col_y:
                    if st.button("⭐ Rate", key=f"rate_{movie_id}", use_container_width=True):
                        st.session_state.action_movie_id = movie_id
                        st.session_state.action_type = "rate"
                        st.rerun()
                
                with col_z:
                    if st.button("ℹ️ Details", key=f"info_{movie_id}", use_container_width=True):
                        st.session_state.selected_movie = movie_id
                        st.rerun()
        
        st.divider()


def render_compact_movie_card(movie: Dict[str, Any]):
    """
    Render a compact movie card for watchlist/sidebar display.
    
    Args:
        movie: Movie data dict
    """
    movie_id = movie.get("id") or movie.get("movie_id")
    title = movie.get("title", "Unknown")
    year = movie.get("release_year", "")
    rating = movie.get("tmdb_rating", 0)
    priority = movie.get("priority", 5)
    
    with st.container():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"**{title}** ({year})")
            st.caption(f"⭐ {rating:.1f} | Priority: {priority}/10")
        
        with col2:
            if st.button("👁️", key=f"view_{movie_id}", use_container_width=True):
                st.session_state.selected_movie = movie_id
                st.rerun()


def render_movie_grid(movies: list, show_actions: bool = True):
    """
    Render movies in a grid layout (2 columns).
    
    Args:
        movies: List of movie dicts
        show_actions: Whether to show action buttons
    """
    if not movies:
        st.info("No movies to display")
        return
    
    # Render in pairs
    for i in range(0, len(movies), 2):
        col1, col2 = st.columns(2)
        
        with col1:
            if i < len(movies):
                render_movie_card(movies[i], show_actions=show_actions)
        
        with col2:
            if i + 1 < len(movies):
                render_movie_card(movies[i + 1], show_actions=show_actions)


def render_movie_list(movies: list, show_similarity: bool = False):
    """
    Render movies in a vertical list.
    
    Args:
        movies: List of movie dicts
        show_similarity: Whether to show similarity scores
    """
    if not movies:
        st.info("No movies found")
        return
    
    for movie in movies:
        similarity = movie.get("similarity") if show_similarity else None
        render_movie_card(movie, show_actions=True, similarity_score=similarity)
