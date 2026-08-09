"""
One-time script to store TMDB API key and Lakebase URL in Databricks secrets.

Run from a notebook:
    %sh python setup_secrets.py

Or from a cluster terminal:
    python setup_secrets.py
"""

import getpass

from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

TMDB_SCOPE = "tmdb"
TMDB_KEY = "api-key"

DB_SCOPE = "database"
DB_KEY = "movie-lakebase-url"

print("📝 TMDB API Secret Setup")
print("=" * 50)
print(f"Scope: {TMDB_SCOPE}")
print(f"Key:   {TMDB_KEY}")
print()

# Create scopes if they don't exist
try:
    w.secrets.create_scope(scope=TMDB_SCOPE)
    print(f"✅ Created secret scope: {TMDB_SCOPE}")
except Exception:
    print(f"ℹ️  Secret scope {TMDB_SCOPE} already exists")

try:
    w.secrets.create_scope(scope=DB_SCOPE)
    print(f"✅ Created secret scope: {DB_SCOPE}")
except Exception:
    print(f"ℹ️  Secret scope {DB_SCOPE} already exists")

print()

# Get TMDB API key
tmdb_api_key = getpass.getpass("Enter your TMDB API key: ")
if tmdb_api_key:
    w.secrets.put_secret(scope=TMDB_SCOPE, key=TMDB_KEY, string_value=tmdb_api_key)
    print(f"✅ Stored TMDB API key in {TMDB_SCOPE}/{TMDB_KEY}")
else:
    print("⚠️  No TMDB API key provided")

print()

# Get Lakebase URL
print("📝 Lakebase Connection URL")
print("=" * 50)
print(f"Scope: {DB_SCOPE}")
print(f"Key:   {DB_KEY}")
print()
print("Format: postgresql://user:password@host:5432/databricks_postgres?sslmode=require")
print()

lakebase_url = getpass.getpass("Enter your Lakebase connection URL: ")
if lakebase_url:
    w.secrets.put_secret(scope=DB_SCOPE, key=DB_KEY, string_value=lakebase_url)
    print(f"✅ Stored Lakebase URL in {DB_SCOPE}/{DB_KEY}")
else:
    print("⚠️  No Lakebase URL provided")

print()
print("🎉 Setup complete!")
