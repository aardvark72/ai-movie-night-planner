"""
LangGraph Agent Implementation - Using Databricks Foundation Models

Main agent orchestrator using LangGraph with Databricks Foundation Model API.
"""

from typing import TypedDict, Annotated, Sequence, List, Dict, Any
import operator
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_community.chat_models import ChatDatabricks
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool

from agent.config import AGENT_SYSTEM_PROMPT, AGENT_CONFIG
from agent.tools import (
    search_movies, SearchMoviesInput,
    get_group_preferences,
    add_to_watchlist, AddToWatchlistInput,
    record_rating, RecordRatingInput,
    explain_recommendation,
    compare_movies
)


# ============================================================================
# Agent State
# ============================================================================

class AgentState(TypedDict):
    """The state of the agent, passed between nodes."""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    current_group_id: int | None  # Track current group for context


# ============================================================================
# Convert Tools to LangChain Format
# ============================================================================

@tool
def search_movies_tool(query: str, group_id: int = None, max_runtime: int = None, 
                       min_rating: float = None, limit: int = 10) -> Dict[str, Any]:
    """
    Search for movies using natural language. Returns semantic matches ranked by similarity.
    
    Args:
        query: Natural language movie search query (e.g., "epic space adventure")
        group_id: Optional group ID to exclude already-watched movies
        max_runtime: Maximum runtime in minutes
        min_rating: Minimum TMDB rating (0-10)
        limit: Maximum number of results (default: 10)
    """
    return search_movies(SearchMoviesInput(
        query=query,
        group_id=group_id,
        max_runtime=max_runtime,
        min_rating=min_rating,
        limit=limit
    ))


@tool
def get_group_preferences_tool(group_id: int) -> Dict[str, Any]:
    """
    Analyze a group's viewing history and preferences.
    
    Args:
        group_id: The group ID to analyze
        
    Returns:
        Top genres, favorite movies, and average runtime preference
    """
    return get_group_preferences(group_id)


@tool
def add_to_watchlist_tool(group_id: int, movie_id: int, added_by: int, 
                         notes: str = None, priority: int = 5) -> Dict[str, Any]:
    """
    Add a movie to a group's watchlist.
    
    Args:
        group_id: The group ID
        movie_id: The movie ID to add
        added_by: User ID who is adding it
        notes: Optional notes about the movie
        priority: Priority level 1-10 (default: 5)
    """
    return add_to_watchlist(AddToWatchlistInput(
        group_id=group_id,
        movie_id=movie_id,
        added_by=added_by,
        notes=notes,
        priority=priority
    ))


@tool
def record_rating_tool(user_id: int, movie_id: int, rating: float, 
                      review_text: str = None, watched_date: str = None) -> Dict[str, Any]:
    """
    Record a user's rating after watching a movie.
    
    Args:
        user_id: The user ID
        movie_id: The movie ID
        rating: Rating from 0.5 to 5.0 stars
        review_text: Optional review text
        watched_date: Date watched in YYYY-MM-DD format
    """
    return record_rating(RecordRatingInput(
        user_id=user_id,
        movie_id=movie_id,
        rating=rating,
        review_text=review_text,
        watched_date=watched_date
    ))


@tool
def explain_recommendation_tool(movie_id: int, group_id: int, user_query: str) -> Dict[str, Any]:
    """
    Explain why a movie was recommended to a group.
    
    Args:
        movie_id: The movie ID to explain
        group_id: The group ID
        user_query: The original search query for context
        
    Returns:
        Detailed explanation with similarity score and preference fit
    """
    return explain_recommendation(movie_id, group_id, user_query)


@tool
def compare_movies_tool(movie_ids: List[int], group_id: int) -> Dict[str, Any]:
    """
    Compare multiple movies for group decision-making.
    
    Args:
        movie_ids: List of 2-4 movie IDs to compare
        group_id: The group ID for preference context
        
    Returns:
        Side-by-side comparison with pros/cons and recommendation
    """
    return compare_movies(movie_ids, group_id)


# List of all tools
TOOLS = [
    search_movies_tool,
    get_group_preferences_tool,
    add_to_watchlist_tool,
    record_rating_tool,
    explain_recommendation_tool,
    compare_movies_tool
]


# ============================================================================
# Agent Graph Nodes
# ============================================================================

def should_continue(state: AgentState) -> str:
    """Decide whether to continue with tools or end."""
    messages = state["messages"]
    last_message = messages[-1]
    
    # If the last message has tool calls, continue to tools
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "continue"
    # Otherwise, end
    return "end"


def call_model(state: AgentState):
    """Call the LLM with the current state."""
    messages = state["messages"]
    
    # Initialize Databricks Foundation Model
    # Using DBRX-Instruct which is free and very capable
    model = ChatDatabricks(
        endpoint="databricks-dbrx-instruct",
        temperature=AGENT_CONFIG["temperature"],
        max_tokens=2000
    ).bind_tools(TOOLS)
    
    # Add system prompt as first message if not present
    if not messages or not isinstance(messages[0].content, str) or AGENT_SYSTEM_PROMPT not in messages[0].content:
        messages = [HumanMessage(content=AGENT_SYSTEM_PROMPT)] + list(messages)
    
    response = model.invoke(messages)
    
    # Return updated state
    return {"messages": [response]}


# ============================================================================
# Build Agent Graph
# ============================================================================

def create_agent_graph():
    """Create the LangGraph agent graph."""
    
    # Define the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode(TOOLS))
    
    # Set entry point
    workflow.set_entry_point("agent")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "continue": "tools",
            "end": END
        }
    )
    
    # Add edge from tools back to agent
    workflow.add_edge("tools", "agent")
    
    # Compile the graph
    return workflow.compile()


# ============================================================================
# Agent Runner
# ============================================================================

class MovieAgent:
    """Main agent class for movie recommendations."""
    
    def __init__(self, group_id: int = None):
        """
        Initialize the movie agent.
        
        Args:
            group_id: Default group ID for recommendations
        """
        self.graph = create_agent_graph()
        self.group_id = group_id
    
    def run(self, message: str, group_id: int = None) -> str:
        """
        Run the agent with a user message.
        
        Args:
            message: User's input message
            group_id: Optional group ID to override default
            
        Returns:
            Agent's response as a string
        """
        # Use provided group_id or fall back to default
        current_group_id = group_id or self.group_id
        
        # Create initial state
        initial_state = {
            "messages": [HumanMessage(content=message)],
            "current_group_id": current_group_id
        }
        
        # Run the graph
        result = self.graph.invoke(initial_state)
        
        # Extract final response
        final_message = result["messages"][-1]
        return final_message.content
    
    def stream(self, message: str, group_id: int = None):
        """
        Stream the agent's response token by token.
        
        Args:
            message: User's input message
            group_id: Optional group ID to override default
            
        Yields:
            Response tokens as they're generated
        """
        current_group_id = group_id or self.group_id
        
        initial_state = {
            "messages": [HumanMessage(content=message)],
            "current_group_id": current_group_id
        }
        
        for chunk in self.graph.stream(initial_state):
            # Yield agent responses
            if "agent" in chunk:
                message = chunk["agent"]["messages"][-1]
                if hasattr(message, "content") and message.content:
                    yield message.content


# ============================================================================
# Convenience Functions
# ============================================================================

def chat(message: str, group_id: int = 1) -> str:
    """
    Quick chat function for testing.
    
    Args:
        message: User message
        group_id: Group ID (default: 1)
        
    Returns:
        Agent response
    """
    agent = MovieAgent(group_id=group_id)
    return agent.run(message)


def create_agent(group_id: int = None) -> MovieAgent:
    """
    Create a new agent instance.
    
    Args:
        group_id: Optional default group ID
        
    Returns:
        MovieAgent instance
    """
    return MovieAgent(group_id=group_id)
