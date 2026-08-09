"""
LangGraph Agent Implementation - Using Databricks Foundation Models

Main agent orchestrator using LangGraph with Databricks Foundation Model API.
"""

from typing import TypedDict, Annotated, Sequence, List, Dict, Any, Optional
import operator
import os
import json
import requests
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, ToolCall
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.outputs import ChatResult, ChatGeneration
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool, BaseTool

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
# Custom ChatDatabricks Implementation
# ============================================================================

class ChatDatabricks(BaseChatModel):
    """Custom Databricks Foundation Model chat wrapper with tool calling support."""
    
    endpoint: str = "databricks-dbrx-instruct"
    temperature: float = 0.7
    max_tokens: int = 2000
    tools: Optional[List[Dict[str, Any]]] = None
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: List[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate chat response using Databricks Foundation Model API."""
        
        # Get Databricks credentials from environment
        host = os.environ.get("DATABRICKS_HOST")
        token = os.environ.get("DATABRICKS_TOKEN") or self._get_oauth_token()
        
        # Convert messages to API format
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                formatted_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                msg_dict = {"role": "assistant", "content": msg.content or ""}
                # Include tool calls if present
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    msg_dict["tool_calls"] = [
                        {
                            "id": tc.get("id", f"call_{i}"),
                            "type": "function",
                            "function": {
                                "name": tc.get("name", ""),
                                "arguments": json.dumps(tc.get("args", {}))
                            }
                        }
                        for i, tc in enumerate(msg.tool_calls)
                    ]
                formatted_messages.append(msg_dict)
            elif isinstance(msg, ToolMessage):
                formatted_messages.append({
                    "role": "tool",
                    "tool_call_id": msg.tool_call_id,
                    "content": msg.content
                })
        
        # Call Databricks serving endpoint
        url = f"https://{host}/serving-endpoints/{self.endpoint}/invocations"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messages": formatted_messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        # Add tools if bound
        if self.tools:
            payload["tools"] = self.tools
            payload["tool_choice"] = "auto"
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        response_message = result["choices"][0]["message"]
        
        # Extract content and tool calls
        content = response_message.get("content") or ""
        tool_calls_data = response_message.get("tool_calls", [])
        
        # Build AIMessage with tool calls if present
        if tool_calls_data:
            tool_calls = []
            for tc in tool_calls_data:
                tool_calls.append({
                    "name": tc["function"]["name"],
                    "args": json.loads(tc["function"]["arguments"]),
                    "id": tc.get("id", f"call_{tc['function']['name']}")
                })
            message = AIMessage(content=content, tool_calls=tool_calls)
        else:
            message = AIMessage(content=content)
        
        generation = ChatGeneration(message=message)
        return ChatResult(generations=[generation])
    
    def _get_oauth_token(self) -> str:
        """Get OAuth token from Databricks Apps environment."""
        client_id = os.environ.get("DATABRICKS_CLIENT_ID")
        client_secret = os.environ.get("DATABRICKS_CLIENT_SECRET")
        host = os.environ.get("DATABRICKS_HOST")
        
        if not all([client_id, client_secret, host]):
            raise ValueError("Missing Databricks credentials in environment")
        
        # Get OAuth token
        token_url = f"https://{host}/oidc/v1/token"
        token_response = requests.post(
            token_url,
            data={
                "grant_type": "client_credentials",
                "scope": "all-apis"
            },
            auth=(client_id, client_secret)
        )
        token_response.raise_for_status()
        return token_response.json()["access_token"]
    
    @property
    def _llm_type(self) -> str:
        return "databricks"
    
    def bind_tools(self, tools: List[BaseTool], **kwargs: Any) -> "ChatDatabricks":
        """Bind tools to this chat model for function calling."""
        # Convert LangChain tools to OpenAI format
        formatted_tools = []
        for tool in tools:
            # Get tool schema
            tool_schema = tool.args_schema.schema() if hasattr(tool, 'args_schema') and tool.args_schema else {}
            
            formatted_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": {
                        "type": "object",
                        "properties": tool_schema.get("properties", {}),
                        "required": tool_schema.get("required", [])
                    }
                }
            })
        
        # Create a new instance with tools
        return ChatDatabricks(
            endpoint=self.endpoint,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            tools=formatted_tools
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
