"""
Session State Management

Utilities for managing Streamlit session state including chat history,
current group, and UI state.
"""

import streamlit as st
from typing import List, Dict, Any


def initialize_session_state():
    """Initialize all session state variables."""
    
    # Chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Current group
    if "current_group_id" not in st.session_state:
        st.session_state.current_group_id = 1  # Default to group 1
    
    # Watchlist cache
    if "watchlist" not in st.session_state:
        st.session_state.watchlist = []
    
    # Group preferences cache
    if "group_preferences" not in st.session_state:
        st.session_state.group_preferences = None
    
    # Current user (for ratings/watchlist additions)
    if "current_user_id" not in st.session_state:
        st.session_state.current_user_id = 1  # Default user
    
    # UI state
    if "show_watchlist" not in st.session_state:
        st.session_state.show_watchlist = False
    
    if "selected_movie" not in st.session_state:
        st.session_state.selected_movie = None


def add_message(role: str, content: str, metadata: Dict[str, Any] = None):
    """
    Add a message to chat history.
    
    Args:
        role: "user" or "assistant"
        content: Message text
        metadata: Optional metadata (movies, tool calls, etc.)
    """
    message = {
        "role": role,
        "content": content,
        "metadata": metadata or {}
    }
    st.session_state.messages.append(message)


def clear_chat():
    """Clear chat history."""
    st.session_state.messages = []


def get_chat_history() -> List[Dict[str, Any]]:
    """Get full chat history."""
    return st.session_state.messages


def set_current_group(group_id: int):
    """
    Set the current group and clear cached data.
    
    Args:
        group_id: The group ID to switch to
    """
    st.session_state.current_group_id = group_id
    st.session_state.group_preferences = None
    st.session_state.watchlist = []


def update_watchlist(watchlist_items: List[Dict[str, Any]]):
    """
    Update the watchlist cache.
    
    Args:
        watchlist_items: List of watchlist items from the database
    """
    st.session_state.watchlist = watchlist_items


def get_watchlist() -> List[Dict[str, Any]]:
    """Get current watchlist."""
    return st.session_state.watchlist


def set_group_preferences(preferences: Dict[str, Any]):
    """
    Cache group preferences.
    
    Args:
        preferences: Group preferences data
    """
    st.session_state.group_preferences = preferences


def get_group_preferences() -> Dict[str, Any]:
    """Get cached group preferences."""
    return st.session_state.group_preferences


def toggle_watchlist():
    """Toggle watchlist sidebar visibility."""
    st.session_state.show_watchlist = not st.session_state.show_watchlist


def select_movie(movie_id: int):
    """
    Select a movie for detailed view.
    
    Args:
        movie_id: The movie ID to select
    """
    st.session_state.selected_movie = movie_id


def clear_selection():
    """Clear movie selection."""
    st.session_state.selected_movie = None
