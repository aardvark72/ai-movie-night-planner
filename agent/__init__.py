"""
Movie Recommendation Agent

A conversational AI agent that helps groups discover movies they'll love.
Built with LangGraph and powered by semantic search over a movie database.
"""

from agent.agent import MovieAgent, create_agent, chat
from agent.config import AGENT_SYSTEM_PROMPT, AGENT_CONFIG

__all__ = [
    'MovieAgent',
    'create_agent', 
    'chat',
    'AGENT_SYSTEM_PROMPT',
    'AGENT_CONFIG'
]

__version__ = '1.0.0'
