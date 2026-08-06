# Lakebase Database Connection Details

## Project Information
- **Project Name**: movie-night
- **Branch**: production  
- **Database**: movienight
- **Schema**: movie_night

## Connection Details
- **Host**: ep-fragrant-waterfall-d8ycnkc8.database.us-east-2.cloud.databricks.com
- **Port**: 5432
- **SSL Mode**: require

## Database Schema
The database uses a dedicated `movie_night` schema with the following tables:

1. **users** - User accounts
2. **groups** - Viewing groups  
3. **group_members** - User-group membership (many-to-many)
4. **movies** - Movie metadata + embeddings (VECTOR COLUMN)
5. **ratings** - User movie ratings
6. **watchlist_items** - Group watchlists  
7. **recommendations** - Agent recommendation history

## Features
- ✓ pgvector extension enabled
- ✓ HNSW index on movie embeddings for fast similarity search
- ✓ Postgres arrays for genres, keywords, cast
- ✓ JSONB for streaming providers and raw API data
- ✓ Foreign key constraints with CASCADE deletes

## Authentication
Use Databricks OAuth tokens for authentication:

```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
endpoint = "projects/movie-night/branches/production/endpoints/primary"
cred = w.postgres.generate_database_credential(endpoint=endpoint)

# Connect with psycopg2
import psycopg2
conn = psycopg2.connect(
    host="ep-fragrant-waterfall-d8ycnkc8.database.us-east-2.cloud.databricks.com",
    port=5432,
    database="movienight",
    user="<your-email>",
    password=cred.token,
    sslmode='require'
)
```

## Next Steps
1. ✅ Lakebase project created
2. ✅ Database and schema created  
3. ✅ All tables created
4. ⏭️ Populate movies table from TMDB API
5. ⏭️ Build agent tools
6. ⏭️ Create Streamlit app
