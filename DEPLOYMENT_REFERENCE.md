
# AI Movie Night Planner - Databricks UI Deployment Reference

## App Configuration

**App Name:** ai-movie-night-planner
**Display Name:** AI Movie Night Planner
**Description:** AI-powered movie recommendations using Databricks Foundation Models

## Source Code

**Source Path:**
```
/Workspace/Users/jevon.rowan2510@gmail.com/ai-movie-night-planner
```

**Entry Point:**
```
streamlit_app/app.py
```

**Framework:** Streamlit

## Secrets & Environment Variables

### Secret (Required)
- **Name:** LAKEBASE_CONNECTION_URL
- **Scope:** database
- **Key:** movie-lakebase-url

### Environment Variables (Optional - app.yaml has these)
- STREAMLIT_SERVER_PORT=8080
- STREAMLIT_SERVER_ADDRESS=0.0.0.0
- STREAMLIT_SERVER_HEADLESS=true

## Resources

- **CPU:** 2
- **Memory:** 4Gi
- **Python Version:** 3.10

## Dependencies (in requirements.txt)

```
streamlit>=1.28.0
psycopg2-binary>=2.9.9
langchain>=0.1.0
langchain-community>=0.0.10
langgraph>=0.0.20
pydantic>=2.0.0
databricks-sdk>=0.18.0
```

## Project Structure

```
ai-movie-night-planner/
├── app.yaml                 # App configuration
├── requirements.txt         # Python dependencies
├── entrypoint.py           # Streamlit launcher
├── .databricks-ignore      # Files to exclude
├── streamlit_app/
│   └── app.py              # Main Streamlit UI
└── agent/
    ├── agent.py            # MovieAgent class
    └── tools.py            # Tool implementations
```

## Troubleshooting

If deployment fails, check UI logs for:
1. **Import errors** - missing dependencies
2. **Secret access errors** - check secret scope/key
3. **Port binding errors** - ensure port 8080 is configured
4. **Database connection errors** - verify Lakebase URL is correct
5. **Streamlit startup errors** - check entrypoint.py

## After Successful Deployment

Once the test app works, we'll:
1. Restore the full app.py with agent features
2. Test the movie search functionality
3. Verify database connections
4. Enable all MovieAgent tools
