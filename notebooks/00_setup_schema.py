# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# DBTITLE 1,Database Schema Setup - AI Movie Night Planner
# MAGIC %md
# MAGIC # 🎬 AI Movie Night Planner - Database Schema Setup
# MAGIC
# MAGIC This notebook sets up the complete database schema for the AI Movie Night Planner project.
# MAGIC
# MAGIC ## Setup Steps:
# MAGIC
# MAGIC 1. **00_setup_schema.sql** - Create schema and enable pgvector
# MAGIC 2. **01_setup_users.sql** - Users table
# MAGIC 3. **02_setup_groups.sql** - Groups and group_members tables
# MAGIC 4. **03_setup_movies.sql** - Movies table with metadata
# MAGIC 5. **04_setup_ratings.sql** - User ratings table
# MAGIC 6. **05_setup_watchlist.sql** - Group watchlist table
# MAGIC 7. **06_setup_embeddings.sql** - Movie embeddings with pgvector
# MAGIC 8. **07_create_indexes.sql** - Performance indexes
# MAGIC
# MAGIC ## Prerequisites:
# MAGIC
# MAGIC * Lakebase instance created and running
# MAGIC * Connection URL stored in `database/movie-lakebase-url` secret
# MAGIC * pgvector extension available
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC **Run the cells below in order to set up the complete database.**

# COMMAND ----------

# DBTITLE 1,Install dependencies
# Install required packages
# Using pg8000 instead of psycopg2 for serverless compatibility
%pip install pg8000 pgvector databricks-sdk --quiet

# COMMAND ----------

# DBTITLE 1,Import libraries and setup connection
from databricks.sdk import WorkspaceClient

print("🔑 Loading Lakebase connection from secrets...")

# Get connection URL from secrets
w = WorkspaceClient()
try:
    LAKEBASE_URL = dbutils.secrets.get(scope="database", key="movie-lakebase-url")
    print(f"✅ Connection URL loaded from secrets")
    
    # Parse connection URL to show host
    if '@' in LAKEBASE_URL:
        host_part = LAKEBASE_URL.split('@')[1].split('/')[0]
        print(f"   Host: {host_part}")
except Exception as e:
    print(f"❌ Failed to load secret: {e}")
    print("\nMake sure to run the 00_setup_secrets notebook first!")
    raise

print("\n✅ Setup complete!")
print("\nNote: Connection will be established when running SQL files.")
print("If you encounter connection issues, check:")
print("  1. Lakebase instance is running")
print("  2. Connection URL format is correct")
print("  3. Credentials are valid")

# COMMAND ----------

# DBTITLE 1,Debug: Verify password in URL
import urllib.parse

# Debug: Check if password is in the URL
parsed = urllib.parse.urlparse(LAKEBASE_URL)
print("\n🔍 Debugging connection URL:")
print(f"  Username: {parsed.username}")
print(f"  Password: {'***PRESENT***' if parsed.password else '❌ MISSING'}")
if parsed.password:
    print(f"  Password length: {len(parsed.password)} characters")
print(f"  Hostname: {parsed.hostname}")
print(f"  Database: {parsed.path.lstrip('/').split('?')[0]}")

if not parsed.password:
    print("\n⚠️ ERROR: No password in connection URL!")
    print("\nThe secret 'database/movie-lakebase-url' needs to be updated.")
    print("Expected format: postgresql://username:password@host:port/database?sslmode=require")
    print("\nPlease run the 00_setup_secrets notebook again with the updated .env file.")

# COMMAND ----------

# DBTITLE 1,Helper function to run SQL files
import pg8000.native
import urllib.parse

def run_sql_file(filename: str):
    """Execute a SQL file against Lakebase."""
    sql_path = f"/Workspace/Users/{w.current_user.me().user_name}/ai-movie-night-planner/sql/{filename}"
    
    print(f"\n{'='*60}")
    print(f"Running: {filename}")
    print(f"{'='*60}")
    
    # Read SQL file
    with open(sql_path, 'r') as f:
        sql_content = f.read()
    
    # Parse connection URL for pg8000
    # Format: postgresql://user:password@host:port/database?params
    parsed = urllib.parse.urlparse(LAKEBASE_URL)
    
    # Extract and decode credentials (URL may have encoded special characters)
    username = urllib.parse.unquote(parsed.username) if parsed.username else None
    password = urllib.parse.unquote(parsed.password) if parsed.password else None
    database = parsed.path.lstrip('/').split('?')[0]
    
    # Parse SSL parameters from query string
    params = urllib.parse.parse_qs(parsed.query)
    ssl_context = params.get('sslmode', ['require'])[0] != 'disable'
    
    # Connect and execute using pg8000
    conn = pg8000.native.Connection(
        user=username,
        password=password,
        host=parsed.hostname,
        port=parsed.port or 5432,
        database=database,
        ssl_context=ssl_context
    )
    
    try:
        # pg8000 native interface uses run() method
        conn.run(sql_content)
        print("\n✅ SQL executed successfully")
    except Exception as e:
        print(f"\n❌ Error executing SQL: {e}")
        raise
    finally:
        conn.close()
    
    print(f"✅ Completed: {filename}\n")

# COMMAND ----------

# DBTITLE 1,Step 0: Create schema and enable pgvector
run_sql_file("00_setup_schema.sql")

# COMMAND ----------

# DBTITLE 1,Step 1: Create users table
run_sql_file("01_setup_users.sql")

# COMMAND ----------

# DBTITLE 1,Step 2: Create groups tables
run_sql_file("02_setup_groups.sql")

# COMMAND ----------

# DBTITLE 1,Step 3: Create movies table
run_sql_file("03_setup_movies.sql")

# COMMAND ----------

# DBTITLE 1,Step 4: Create ratings table
run_sql_file("04_setup_ratings.sql")

# COMMAND ----------

# DBTITLE 1,Step 5: Create watchlist table
run_sql_file("05_setup_watchlist.sql")

# COMMAND ----------

# DBTITLE 1,Step 6: Create embeddings table
run_sql_file("06_setup_embeddings.sql")

# COMMAND ----------

# DBTITLE 1,Step 7: Create performance indexes
run_sql_file("07_create_indexes.sql")

# COMMAND ----------

# DBTITLE 1,Verification: Check schema
# Verify all tables were created
import pg8000.native
import urllib.parse

# Parse connection URL for pg8000
parsed = urllib.parse.urlparse(LAKEBASE_URL)

# Extract and decode credentials
username = urllib.parse.unquote(parsed.username) if parsed.username else None
password = urllib.parse.unquote(parsed.password) if parsed.password else None
database = parsed.path.lstrip('/').split('?')[0]

# Parse SSL parameters from query string
params = urllib.parse.parse_qs(parsed.query)
ssl_context = params.get('sslmode', ['require'])[0] != 'disable'

conn = pg8000.native.Connection(
    user=username,
    password=password,
    host=parsed.hostname,
    port=parsed.port or 5432,
    database=database,
    ssl_context=ssl_context
)
try:
    # Query tables using pg8000 native interface
    tables = conn.run("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'movie_night'
        ORDER BY table_name
    """)
    
    print("\n" + "="*60)
    print("📋 Database Schema Created Successfully!")
    print("="*60)
    print(f"\nTables in 'movie_night' schema ({len(tables)}):")
    for table in tables:
        print(f"  ✅ {table[0]}")
    
    # Set search path
    conn.run("SET search_path TO movie_night, public")
    
    # Count sample data
    counts = conn.run("""
        SELECT 
            (SELECT COUNT(*) FROM users) as users,
            (SELECT COUNT(*) FROM groups) as groups,
            (SELECT COUNT(*) FROM movies) as movies,
            (SELECT COUNT(*) FROM ratings) as ratings,
            (SELECT COUNT(*) FROM watchlist_items) as watchlist_items
    """)
    
    if counts:
        count_row = counts[0]
        print("\n📊 Sample Data Counts:")
        print(f"  Users: {count_row[0]}")
        print(f"  Groups: {count_row[1]}")
        print(f"  Movies: {count_row[2]}")
        print(f"  Ratings: {count_row[3]}")
        print(f"  Watchlist Items: {count_row[4]}")
    
    print("\n✅ Database setup complete!")
    print("\nNext steps:")
    print("  1. Run 01_ingest_tmdb_movies.py to fetch movies from TMDB")
    print("  2. Run 02_generate_embeddings.py to create vector embeddings")
    print("  3. Deploy the Databricks App")
finally:
    conn.close()