"""
Watchlist Component

Displays and manages the group's watchlist in a sidebar.
"""

import streamlit as st
from typing import Dict, Any, List
from streamlit_app.components.movie_card import render_compact_movie_card


def render_watchlist_sidebar(watchlist_items: List[Dict[str, Any]]):
    """
    Render the watchlist in a sidebar.
    
    Args:
        watchlist_items: List of watchlist items with movie data
    """
    
    st.sidebar.title("🍿 Watchlist")
    
    if not watchlist_items:
        st.sidebar.info("Your watchlist is empty. Ask MovieMate to add some movies!")
        return
    
    # Sort by priority (highest first)
    sorted_items = sorted(
        watchlist_items, 
        key=lambda x: x.get("priority", 5), 
        reverse=True
    )
    
    st.sidebar.caption(f"**{len(sorted_items)} movies** on your list")
    
    # Filters
    with st.sidebar.expander("🔍 Filter Watchlist"):
        min_priority = st.slider(
            "Minimum Priority",
            min_value=1,
            max_value=10,
            value=1,
            key="watchlist_filter_priority"
        )
    
    # Filter and display
    filtered_items = [
        item for item in sorted_items 
        if item.get("priority", 5) >= min_priority
    ]
    
    if not filtered_items:
        st.sidebar.warning(f"No movies with priority ≥ {min_priority}")
        return
    
    st.sidebar.caption(f"Showing {len(filtered_items)} movies")
    
    # Render each item
    for item in filtered_items:
        with st.sidebar.container():
            render_watchlist_item(item)


def render_watchlist_item(item: Dict[str, Any]):
    """
    Render a single watchlist item.
    
    Args:
        item: Watchlist item with movie data
    """
    movie_id = item.get("movie_id") or item.get("id")
    title = item.get("title", "Unknown")
    year = item.get("release_year", "")
    rating = item.get("tmdb_rating", 0)
    priority = item.get("priority", 5)
    notes = item.get("notes")
    
    # Priority indicator
    priority_emoji = "🔥" if priority >= 8 else "⭐" if priority >= 5 else "📌"
    
    with st.container():
        # Title and basic info
        st.markdown(f"{priority_emoji} **{title}**")
        
        col1, col2 = st.columns(2)
        with col1:
            st.caption(f"📅 {year}")
        with col2:
            st.caption(f"⭐ {rating:.1f}")
        
        # Priority bar
        st.progress(priority / 10, text=f"Priority: {priority}/10")
        
        # Notes
        if notes:
            with st.expander("📝 Notes"):
                st.caption(notes)
        
        # Actions
        col_a, col_b = st.columns(2)
        
        with col_a:
            if st.button("👁️ View", key=f"wl_view_{movie_id}", use_container_width=True):
                st.session_state.selected_movie = movie_id
                st.rerun()
        
        with col_b:
            if st.button("✅ Watched", key=f"wl_watched_{movie_id}", use_container_width=True):
                st.session_state.action_movie_id = movie_id
                st.session_state.action_type = "mark_watched"
                st.rerun()
        
        st.divider()


def render_watchlist_page(watchlist_items: List[Dict[str, Any]]):
    """
    Render watchlist as a main page (not sidebar).
    
    Args:
        watchlist_items: List of watchlist items
    """
    st.title("🍿 Group Watchlist")
    
    if not watchlist_items:
        st.info("Your watchlist is empty. Ask MovieMate to add some movies!")
        
        # Suggestions
        st.markdown("### 💡 Try asking:")
        suggestions = [
            "Find me some action movies",
            "What are some highly-rated comedies?",
            "Show me movies like Inception",
            "Find something under 2 hours"
        ]
        for suggestion in suggestions:
            st.markdown(f"- {suggestion}")
        return
    
    # Stats
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Movies", len(watchlist_items))
    
    with col2:
        high_priority = sum(1 for item in watchlist_items if item.get("priority", 5) >= 8)
        st.metric("High Priority", high_priority)
    
    with col3:
        avg_rating = sum(item.get("tmdb_rating", 0) for item in watchlist_items) / len(watchlist_items)
        st.metric("Avg Rating", f"{avg_rating:.1f}")
    
    st.divider()
    
    # Sort options
    col_a, col_b = st.columns([2, 1])
    
    with col_a:
        sort_by = st.selectbox(
            "Sort by",
            ["Priority (High to Low)", "Priority (Low to High)", 
             "Rating (High to Low)", "Recently Added"],
            key="watchlist_sort"
        )
    
    # Sort watchlist
    if sort_by == "Priority (High to Low)":
        sorted_items = sorted(watchlist_items, key=lambda x: x.get("priority", 5), reverse=True)
    elif sort_by == "Priority (Low to High)":
        sorted_items = sorted(watchlist_items, key=lambda x: x.get("priority", 5))
    elif sort_by == "Rating (High to Low)":
        sorted_items = sorted(watchlist_items, key=lambda x: x.get("tmdb_rating", 0), reverse=True)
    else:  # Recently Added
        sorted_items = watchlist_items  # Already chronological from DB
    
    # Render movies
    from streamlit_app.components.movie_card import render_movie_list
    
    # Add watchlist metadata to each item
    for item in sorted_items:
        item["_is_watchlist_item"] = True
    
    render_movie_list(sorted_items, show_similarity=False)
