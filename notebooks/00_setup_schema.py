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
%pip install psycopg2-binary pgvector databricks-sdk --quiet

# COMMAND ----------

# DBTITLE 1,Import libraries and setup connection
import psycopg2
from databricks.sdk import WorkspaceClient

print("🔑 Loading Lakebase connection from secrets...")

# Get connection URL from secrets
w = WorkspaceClient()
secret = w.secrets.get_secret(scope="database", key="movie-lakebase-url")

# Decode the base64-encoded URL
import base64
try:
    LAKEBASE_URL = base64.b64decode(secret.value).decode('utf-8')
except:
    # If decode fails, it might already be decoded
    LAKEBASE_URL = secret.value

print(f"✅ Connection URL loaded")
print(f"   Host: {LAKEBASE_URL.split('@')[1].split('/')[0] if '@' in LAKEBASE_URL else 'configured'}")

# Test connection
print("\n🔌 Testing connection...")
conn = psycopg2.connect(LAKEBASE_URL, connect_timeout=10)
cursor = conn.cursor()
cursor.execute("SELECT version()")
version = cursor.fetchone()[0]
cursor.close()
conn.close()

print(f"✅ Connection successful!")
print(f"   PostgreSQL: {version[:50]}...")

# COMMAND ----------

# DBTITLE 1,Helper function to run SQL files
def run_sql_file(filename: str):
    """Execute a SQL file against Lakebase."""
    sql_path = f"/Workspace/Users/{w.current_user.me().user_name}/ai-movie-night-planner/sql/{filename}"
    
    print(f"\n{'='*60}")
    print(f"Running: {filename}")
    print(f"{'='*60}")
    
    # Read SQL file
    with open(sql_path, 'r') as f:
        sql_content = f.read()
    
    # Connect and execute
    conn = psycopg2.connect(LAKEBASE_URL)
    try:
        with conn.cursor() as cur:
            # Execute the entire file
            cur.execute(sql_content)
            conn.commit()
            
            # If there are results, fetch and display them
            if cur.description:
                rows = cur.fetchall()
                if rows:
                    print(f"\n✅ Results ({len(rows)} rows):")
                    for row in rows[:10]:  # Show first 10 rows
                        print(row)
                    if len(rows) > 10:
                        print(f"... and {len(rows) - 10} more rows")
                else:
                    print("\n✅ Query executed successfully (no results)")
            else:
                print("\n✅ SQL executed successfully")
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
conn = psycopg2.connect(LAKEBASE_URL)
try:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'movie_night'
            ORDER BY table_name
        """)
        tables = cur.fetchall()
        
        print("\n" + "="*60)
        print("📋 Database Schema Created Successfully!")
        print("="*60)
        print(f"\nTables in 'movie_night' schema ({len(tables)}):")
        for table in tables:
            print(f"  ✅ {table[0]}")
        
        # Count sample data
        cur.execute("""
            SET search_path TO movie_night, public;
            SELECT 
                (SELECT COUNT(*) FROM users) as users,
                (SELECT COUNT(*) FROM groups) as groups,
                (SELECT COUNT(*) FROM movies) as movies,
                (SELECT COUNT(*) FROM ratings) as ratings,
                (SELECT COUNT(*) FROM watchlist_items) as watchlist_items
        """)
        counts = cur.fetchone()
        
        print("\n📊 Sample Data Counts:")
        print(f"  Users: {counts[0]}")
        print(f"  Groups: {counts[1]}")
        print(f"  Movies: {counts[2]}")
        print(f"  Ratings: {counts[3]}")
        print(f"  Watchlist Items: {counts[4]}")
        
        print("\n✅ Database setup complete!")
        print("\nNext steps:")
        print("  1. Run 01_ingest_tmdb_movies.py to fetch movies from TMDB")
        print("  2. Run 02_generate_embeddings.py to create vector embeddings")
        print("  3. Deploy the Databricks App")
finally:
    conn.close()