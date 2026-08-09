"""
AI Movie Night Planner - Main Streamlit App

Interactive chat interface with MovieMate for group movie recommendations.
"""

import streamlit as st
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from streamlit_app.utils.session import (
    initialize_session_state,
    set_current_group,
    clear_chat
)
from streamlit_app.components.chat import (
    render_chat_interface,
    render_quick_actions,
    clear_chat_history
)
from streamlit_app.components.watchlist import (
    render_watchlist_sidebar,
    render_watchlist_page
)


# ============================================================================
# Page Configuration
# ============================================================================

st.set_page_config(
    page_title="AI Movie Night Planner",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================================
# Initialize Session State
# ============================================================================

initialize_session_state()


# ============================================================================
# Sidebar: Group Selector & Watchlist
# ============================================================================

with st.sidebar:
    st.title("🎬 Movie Night Planner")
    
    # Group selector
    st.markdown("### 👥 Your Group")
    
    # Get available groups (hardcoded for now, could query DB)
    groups = {
        1: "The Movie Buffs",
        2: "Friday Night Crew",
        3: "Family Movie Night"
    }
    
    current_group = st.selectbox(
        "Select Group",
        options=list(groups.keys()),
        format_func=lambda x: groups[x],
        index=list(groups.keys()).index(st.session_state.current_group_id),
        key="group_selector"
    )
    
    # Update group if changed
    if current_group != st.session_state.current_group_id:
        set_current_group(current_group)
        st.rerun()
    
    st.divider()
    
    # Page navigation
    st.markdown("### 📑 Navigation")
    
    page = st.radio(
        "Go to",
        ["💬 Chat", "🍿 Watchlist"],
        key="page_nav",
        label_visibility="collapsed"
    )
    
    st.divider()
    
    # Chat controls
    if page == "💬 Chat":
        st.markdown("### ⚙️ Chat Controls")
        
        if st.button("🗑️ Clear Chat", use_container_width=True):
            clear_chat_history()
        
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    st.divider()
    
    # Display watchlist in sidebar (only on chat page)
    if page == "💬 Chat":
        # Load watchlist from agent tools
        try:
            from agent.tools import get_watchlist_items
            watchlist = get_watchlist_items(st.session_state.current_group_id)
            
            if watchlist.get("success"):
                items = watchlist.get("items", [])
                if items:
                    render_watchlist_sidebar(items)
                else:
                    st.info("Watchlist is empty")
            else:
                st.warning("Couldn't load watchlist")
        except Exception as e:
            st.caption(f"Watchlist: {str(e)}")
    
    # Footer
    st.divider()
    st.caption("Powered by MovieMate 🎬")
    st.caption("Built with Databricks & Lakebase")


# ============================================================================
# Main Content Area
# ============================================================================

if page == "💬 Chat":
    # Chat page
    st.title("💬 Chat with MovieMate")
    st.caption(f"Finding movies for: **{groups[current_group]}**")
    
    # Welcome message
    if not st.session_state.messages:
        st.markdown("""
        👋 **Hi! I'm MovieMate**, your friendly movie recommendation assistant.
        
        I can help you:
        - 🔍 Find movies based on what you're in the mood for
        - 🎯 Get personalized recommendations for your group
        - 📝 Manage your watchlist
        - ⭐ Track ratings and reviews
        
        Ask me anything about movies!
        """)
        
        # Quick actions
        render_quick_actions()
        
        st.divider()
    
    # Chat interface
    render_chat_interface()

elif page == "🍿 Watchlist":
    # Watchlist page
    try:
        from agent.tools import get_watchlist_items
        watchlist = get_watchlist_items(st.session_state.current_group_id)
        
        if watchlist.get("success"):
            items = watchlist.get("items", [])
            render_watchlist_page(items)
        else:
            st.error("Failed to load watchlist")
            st.code(watchlist.get("error", "Unknown error"))
    except Exception as e:
        st.error(f"Error loading watchlist: {str(e)}")


# ============================================================================
# Action Handlers (for buttons clicked in components)
# ============================================================================

# Handle add to watchlist action
if "action_type" in st.session_state and st.session_state.action_type == "add_watchlist":
    movie_id = st.session_state.action_movie_id
    
    # Show dialog
    with st.dialog("➕ Add to Watchlist"):
        st.markdown(f"Adding movie ID: **{movie_id}**")
        
        priority = st.slider("Priority", min_value=1, max_value=10, value=5)
        notes = st.text_area("Notes (optional)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Add", type="primary", use_container_width=True):
                # Call add_to_watchlist tool
                try:
                    from agent.tools import add_to_watchlist, AddToWatchlistInput
                    
                    result = add_to_watchlist(AddToWatchlistInput(
                        group_id=st.session_state.current_group_id,
                        movie_id=movie_id,
                        added_by=st.session_state.current_user_id,
                        notes=notes if notes else None,
                        priority=priority
                    ))
                    
                    if result.get("success"):
                        st.success("✅ Added to watchlist!")
                        time.sleep(1)
                        del st.session_state.action_type
                        del st.session_state.action_movie_id
                        st.rerun()
                    else:
                        st.error(f"Failed: {result.get('error')}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        with col2:
            if st.button("Cancel", use_container_width=True):
                del st.session_state.action_type
                del st.session_state.action_movie_id
                st.rerun()

# Handle rate movie action
if "action_type" in st.session_state and st.session_state.action_type == "rate":
    movie_id = st.session_state.action_movie_id
    
    with st.dialog("⭐ Rate Movie"):
        st.markdown(f"Rate movie ID: **{movie_id}**")
        
        rating = st.slider("Rating", min_value=0.5, max_value=5.0, value=3.0, step=0.5)
        review = st.text_area("Review (optional)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Submit Rating", type="primary", use_container_width=True):
                try:
                    from agent.tools import record_rating, RecordRatingInput
                    from datetime import date
                    
                    result = record_rating(RecordRatingInput(
                        user_id=st.session_state.current_user_id,
                        movie_id=movie_id,
                        rating=rating,
                        review_text=review if review else None,
                        watched_date=date.today().isoformat()
                    ))
                    
                    if result.get("success"):
                        st.success("✅ Rating recorded!")
                        time.sleep(1)
                        del st.session_state.action_type
                        del st.session_state.action_movie_id
                        st.rerun()
                    else:
                        st.error(f"Failed: {result.get('error')}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        with col2:
            if st.button("Cancel", use_container_width=True):
                del st.session_state.action_type
                del st.session_state.action_movie_id
                st.rerun()
