"""
Chat Interface Component

Main chat interface for conversing with MovieMate agent.
"""

import streamlit as st
from typing import Dict, Any, List
import time


def render_chat_message(message: Dict[str, Any]):
    """
    Render a single chat message.
    
    Args:
        message: Message dict with role, content, and optional metadata
    """
    role = message["role"]
    content = message["content"]
    metadata = message.get("metadata", {})
    
    # User message
    if role == "user":
        with st.chat_message("user", avatar="👤"):
            st.markdown(content)
    
    # Assistant message
    else:
        with st.chat_message("assistant", avatar="🎬"):
            st.markdown(content)
            
            # Render any movies in metadata
            movies = metadata.get("movies", [])
            if movies:
                st.divider()
                render_movie_results(movies)


def render_movie_results(movies: List[Dict[str, Any]]):
    """
    Render movie search results in chat.
    
    Args:
        movies: List of movie dicts
    """
    if not movies:
        return
    
    # Show first few movies inline
    display_count = min(3, len(movies))
    
    for movie in movies[:display_count]:
        render_inline_movie(movie)
    
    if len(movies) > display_count:
        with st.expander(f"➕ Show {len(movies) - display_count} more movies"):
            for movie in movies[display_count:]:
                render_inline_movie(movie)


def render_inline_movie(movie: Dict[str, Any]):
    """
    Render a compact movie in chat results.
    
    Args:
        movie: Movie data dict
    """
    movie_id = movie.get("id") or movie.get("movie_id")
    title = movie.get("title", "Unknown")
    year = movie.get("release_year", "")
    rating = movie.get("tmdb_rating", 0)
    runtime = movie.get("runtime_minutes", 0)
    genres = movie.get("genres", [])
    similarity = movie.get("similarity")
    
    with st.container():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Title and year
            st.markdown(f"**{title}** ({year})")
            
            # Rating and runtime
            runtime_str = f"{runtime // 60}h {runtime % 60}m" if runtime else "N/A"
            st.caption(f"⭐ {rating:.1f} | ⏱️ {runtime_str}")
            
            # Genres
            if genres:
                genre_str = " · ".join(genres[:3])
                st.caption(f"🎬 {genre_str}")
            
            # Similarity score
            if similarity:
                match_percent = int(similarity * 100)
                st.caption(f"🎯 {match_percent}% match")
        
        with col2:
            # Quick actions
            if st.button("➕", key=f"quick_add_{movie_id}", 
                        help="Add to watchlist", use_container_width=True):
                st.session_state.action_movie_id = movie_id
                st.session_state.action_type = "add_watchlist"
                st.rerun()
            
            if st.button("ℹ️", key=f"quick_info_{movie_id}",
                        help="More info", use_container_width=True):
                st.session_state.selected_movie = movie_id
                st.rerun()
        
        st.divider()


def render_chat_interface():
    """
    Render the main chat interface.
    """
    
    # Chat history
    for message in st.session_state.messages:
        render_chat_message(message)
    
    # Chat input
    if prompt := st.chat_input("Ask MovieMate anything... 🎬"):
        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
            "metadata": {}
        })
        
        # Display user message immediately
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)
        
        # Get agent response
        with st.chat_message("assistant", avatar="🎬"):
            with st.spinner("MovieMate is thinking..."):
                response = get_agent_response(prompt)
                st.markdown(response["content"])
                
                # Show any movies
                if response.get("movies"):
                    st.divider()
                    render_movie_results(response["movies"])
        
        # Add assistant message to history
        st.session_state.messages.append({
            "role": "assistant",
            "content": response["content"],
            "metadata": {"movies": response.get("movies", [])}
        })
        
        st.rerun()


def get_agent_response(user_message: str) -> Dict[str, Any]:
    """
    Get response from MovieMate agent.
    
    Args:
        user_message: User's message
        
    Returns:
        Dict with content and optional movies list
    """
    try:
        # Import agent
        from agent.agent import MovieAgent
        
        # Create agent with current group
        agent = MovieAgent(group_id=st.session_state.current_group_id)
        
        # Get response
        response = agent.run(user_message)
        
        # Parse response for movies (if agent returned structured data)
        # For now, just return the text response
        return {
            "content": response,
            "movies": []  # Agent will mention movies in text
        }
        
    except Exception as e:
        # Fallback response if agent isn't available
        return {
            "content": f"Sorry, I encountered an error: {str(e)}\n\nPlease make sure the agent is properly configured.",
            "movies": []
        }


def render_quick_actions():
    """
    Render quick action buttons for common requests.
    """
    st.markdown("### 💡 Try asking:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🎬 Find a movie", use_container_width=True):
            st.session_state.quick_prompt = "Find me a highly-rated movie"
            st.rerun()
    
    with col2:
        if st.button("🍿 Check watchlist", use_container_width=True):
            st.session_state.quick_prompt = "Show me our watchlist"
            st.rerun()
    
    with col3:
        if st.button("❓ What's good?", use_container_width=True):
            st.session_state.quick_prompt = "What should we watch tonight?"
            st.rerun()
    
    # Sample prompts
    st.caption("Or try these examples:")
    examples = [
        "Find me a funny movie under 2 hours",
        "Show me action movies like John Wick",
        "What are some highly-rated sci-fi films?",
        "Find something the group would enjoy"
    ]
    
    for example in examples:
        st.caption(f"• {example}")


def clear_chat_history():
    """Clear the chat history."""
    st.session_state.messages = []
    st.rerun()
