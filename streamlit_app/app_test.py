"""
Minimal Test - AI Movie Night Planner
"""
import streamlit as st

st.set_page_config(
    page_title="AI Movie Night Planner - Test",
    page_icon="🎬"
)

st.title("🎬 AI Movie Night Planner")
st.write("✅ Streamlit is working!")

# Test environment variables
import os

st.subheader("Environment Variables")
lakebase_url = os.environ.get('LAKEBASE_CONNECTION_URL', 'NOT SET')
databricks_host = os.environ.get('DATABRICKS_HOST', 'NOT SET')
databricks_token = os.environ.get('DATABRICKS_TOKEN', 'NOT SET')

st.write(f"• LAKEBASE_CONNECTION_URL: {'✅ Set' if lakebase_url != 'NOT SET' else '❌ Not Set'}")
st.write(f"• DATABRICKS_HOST: {'✅ Set' if databricks_host != 'NOT SET' else '❌ Not Set'}")
st.write(f"• DATABRICKS_TOKEN: {'✅ Set' if databricks_token != 'NOT SET' else '❌ Not Set'}")

# Test imports
st.subheader("Dependency Check")
try:
    import psycopg2
    st.write("✅ psycopg2")
except Exception as e:
    st.write(f"❌ psycopg2: {e}")

try:
    import langchain
    st.write("✅ langchain")
except Exception as e:
    st.write(f"❌ langchain: {e}")

try:
    import langchain_community
    st.write("✅ langchain_community")
except Exception as e:
    st.write(f"❌ langchain_community: {e}")

try:
    import langgraph
    st.write("✅ langgraph")
except Exception as e:
    st.write(f"❌ langgraph: {e}")

st.success("Test app loaded successfully!")
