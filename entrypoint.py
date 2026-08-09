#!/usr/bin/env python3
"""
Entrypoint for AI Movie Night Planner Streamlit App
"""
import sys
import os

# Ensure we're in the right directory
app_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(app_dir)

# Add to Python path
sys.path.insert(0, app_dir)

# Run Streamlit
if __name__ == "__main__":
    import streamlit.web.cli as stcli
    
    sys.argv = [
        "streamlit",
        "run",
        "streamlit_app/app.py",
        "--server.port=8080",
        "--server.address=0.0.0.0",
        "--server.headless=true",
        "--server.enableCORS=false",
        "--server.enableXsrfProtection=false"
    ]
    
    sys.exit(stcli.main())
