# Movie Recommendation Agent 🎬

A conversational AI agent (MovieMate) that helps groups discover movies they'll love together.

## Features

- **Semantic Search**: Natural language queries like "epic space adventure with aliens"
- **Group-Aware**: Considers group viewing history and preferences
- **Smart Recommendations**: Balances different tastes within a group
- **Explainable**: Tells you WHY a movie fits your group
- **Watchlist Management**: Add movies to watch later with priority levels
- **Rating System**: Record ratings to improve future recommendations

## Architecture

Built with **LangGraph** (agent orchestration) + **LangChain** (tool calling):

```
User Query
    ↓
[Agent Node] ← System Prompt (MovieMate personality)
    ↓
Decision: Need tools?
    ↓ YES
[Tool Node] → Execute tool (search, preferences, etc.)
    ↓
[Agent Node] ← Tool results
    ↓
Decision: Need more tools?
    ↓ NO
Final Response
```

## Tools Available

1. **search_movies** - Semantic vector search
2. **get_group_preferences** - Analyze viewing history  
3. **explain_recommendation** - Explain why a movie fits
4. **compare_movies** - Compare options side-by-side
5. **add_to_watchlist** - Save for later
6. **record_rating** - Rate watched movies

## Quick Start

### Basic Usage

```python
from agent import chat

# Simple query
response = chat("Find me a funny movie under 2 hours", group_id=1)
print(response)
```

### Advanced Usage

```python
from agent import MovieAgent

# Create agent instance
agent = MovieAgent(group_id=1)

# Single query
response = agent.run("What should we watch tonight?")
print(response)

# Streaming response (real-time)
for token in agent.stream("Find me a thriller"):
    print(token, end="", flush=True)
```

### With Conversation History

```python
agent = MovieAgent(group_id=1)

# Multi-turn conversation
response1 = agent.run("Find me an action movie")
response2 = agent.run("Tell me more about the first one")
response3 = agent.run("Add it to our watchlist")
```

## Configuration

### System Prompt
Located in `config.py`:
- Defines MovieMate personality
- Tool usage guidelines
- Response formatting rules

### Model Settings
```python
AGENT_CONFIG = {
    "model": "gpt-4",           # LLM to use
    "temperature": 0.7,         # Creativity level
    "max_iterations": 10,       # Safety limit
    "verbose": True             # Debug logging
}
```

## Example Interactions

**User**: "We want something funny but not too long"
```
🎬 How about *Spirited*? It's a fun comedy-musical at 127 minutes - 
not too long for a movie night! It's got great energy and won't 
overstay its welcome. Want me to add it to your watchlist?
```

**User**: "Find me a space adventure like Interstellar"
```
Based on your group's love of sci-fi, I think you'd enjoy:

1. **Kingdom of the Planet of the Apes** (2024)
   145 min | 7.1/10 | Sci-Fi, Adventure, Action
   Epic scale and emotional depth similar to Interstellar

2. **Infinite** (2021)  
   106 min | 6.6/10 | Sci-Fi, Action
   Mind-bending concepts and fast-paced action

Both match your group's preference for thoughtful sci-fi. 
Want details on either?
```

## Testing

Run the agent test:
```bash
python -c "from agent import chat; print(chat('Find me a comedy'))"
```

## Next Steps

1. ✅ Agent configuration complete
2. 🎨 Build Streamlit UI (next)
3. 🚀 Deploy as Databricks App V2
