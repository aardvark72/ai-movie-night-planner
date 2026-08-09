"""
Lakebase Postgres Database Utilities

Provides connection utilities and helper functions for interacting with
the Lakebase Postgres database.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional, List, Dict, Any


class LakebaseConnection:
    """
    Manages connections to Lakebase Postgres database.
    
    Usage:
        conn = LakebaseConnection(
            project="movie-night",
            branch="production",
            database="movie_night"
        )
        
        results = conn.query("SELECT * FROM movies LIMIT 10")
    """
    
    def __init__(
        self,
        project: str,
        branch: str = "production",
        endpoint: str = "primary",
        database: str = "databricks_postgres",
        schema: str = "movie_night"
    ):
        """Initialize Lakebase connection.
        
        Args:
            project: Lakebase project ID (e.g., 'movie-night-planner')
            branch: Branch name (default: 'production')
            endpoint: Endpoint name (default: 'primary')
            database: Database name (default: 'databricks_postgres')
            schema: Schema name (default: 'movie_night')
        """
        self.project = project
        self.branch = branch
        self.endpoint = endpoint
        self.database = database
        self.schema = schema
        self._connection = None
        self._cursor = None
    
    def connect(self):
        """Establish connection to Lakebase Postgres."""
        if self._connection:
            return
        
        # Direct connection using host from CONNECTION.md
        # Host: ep-steep-glitter-d84ausgo.database.us-east-2.cloud.databricks.com
        host = "ep-steep-glitter-d84ausgo.database.us-east-2.cloud.databricks.com"
        
        # Get OAuth token using workspace client
        from databricks.sdk import WorkspaceClient
        w = WorkspaceClient()
        
        # Generate token using the generic API (works without postgres attribute)
        try:
            import requests
            import json
            
            # Get workspace host and token
            cfg = w.config
            api_token = cfg.token
            
            if not api_token:
                # Fall back to getting token from current session
                token_response = w.api_client.do(
                    'POST',
                    f'/api/2.0/lakebase/projects/{self.project}/branches/{self.branch}/endpoints/{self.endpoint}/credentials',
                    data={}
                )
                token = token_response.get('token')
            else:
                # Use workspace token as password
                token = api_token
            
            username = w.current_user.me().user_name
        except Exception as e:
            # Fallback: read from secrets if available
            try:
                token = dbutils.secrets.get(scope="database", key="lakebase_token")
                username = dbutils.secrets.get(scope="database", key="lakebase_user")
            except:
                raise Exception(f"Could not get database credentials: {e}")
        
        # Connect
        self._connection = psycopg2.connect(
            host=host,
            dbname=self.database,
            user=username,
            password=token,
            sslmode="require"
        )
        
        # Set search path to schema
        cursor = self._connection.cursor()
        cursor.execute(f"SET search_path TO {self.schema}, public")
        cursor.close()
    
    def query(self, sql: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results as list of dicts.
        
        Args:
            sql: SQL query string
            params: Optional tuple of query parameters
        
        Returns:
            List of result rows as dicts
        """
        if not self._connection:
            self.connect()
        
        cursor = self._connection.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute(sql, params)
            results = cursor.fetchall()
            return [dict(row) for row in results]
        finally:
            cursor.close()
    
    def execute(self, sql: str, params: Optional[tuple] = None, commit: bool = True) -> int:
        """Execute INSERT/UPDATE/DELETE and return affected row count.
        
        Args:
            sql: SQL statement
            params: Optional tuple of parameters
            commit: Whether to commit immediately (default: True)
        
        Returns:
            Number of affected rows
        """
        if not self._connection:
            self.connect()
        
        cursor = self._connection.cursor()
        try:
            cursor.execute(sql, params)
            rowcount = cursor.rowcount
            if commit:
                self._connection.commit()
            return rowcount
        except Exception as e:
            self._connection.rollback()
            raise e
        finally:
            cursor.close()
    
    def executemany(self, sql: str, params_list: List[tuple], commit: bool = True) -> int:
        """Execute same SQL statement with multiple parameter sets.
        
        Args:
            sql: SQL statement
            params_list: List of parameter tuples
            commit: Whether to commit immediately (default: True)
        
        Returns:
            Number of affected rows
        """
        if not self._connection:
            self.connect()
        
        cursor = self._connection.cursor()
        try:
            cursor.executemany(sql, params_list)
            rowcount = cursor.rowcount
            if commit:
                self._connection.commit()
            return rowcount
        except Exception as e:
            self._connection.rollback()
            raise e
        finally:
            cursor.close()
    
    def commit(self):
        """Explicitly commit transaction."""
        if self._connection:
            self._connection.commit()
    
    def rollback(self):
        """Explicitly rollback transaction."""
        if self._connection:
            self._connection.rollback()
    
    def close(self):
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type:
            self.rollback()
        else:
            self.commit()
        self.close()


def insert_movie(conn: LakebaseConnection, movie_data: Dict[str, Any]) -> int:
    """Insert a movie into the database.
    
    Args:
        conn: LakebaseConnection instance
        movie_data: Dict with movie fields
    
    Returns:
        movie_id of inserted movie
    """
    sql = """
    INSERT INTO movies (
        tmdb_id, title, original_title, release_date, runtime,
        overview, tagline, genres, keywords, director, cast_names,
        tmdb_rating, tmdb_vote_count, popularity, content_rating,
        poster_path, backdrop_path, trailer_url, streaming_providers,
        raw_data, is_active
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s, %s
    )
    ON CONFLICT (tmdb_id) DO UPDATE SET
        title = EXCLUDED.title,
        overview = EXCLUDED.overview,
        tmdb_rating = EXCLUDED.tmdb_rating,
        last_updated = CURRENT_TIMESTAMP
    RETURNING movie_id
    """
    
    import json
    
    params = (
        movie_data.get('tmdb_id'),
        movie_data.get('title'),
        movie_data.get('original_title'),
        movie_data.get('release_date'),
        movie_data.get('runtime'),
        movie_data.get('overview'),
        movie_data.get('tagline'),
        movie_data.get('genres'),
        movie_data.get('keywords'),
        movie_data.get('director'),
        movie_data.get('cast_names'),
        movie_data.get('tmdb_rating'),
        movie_data.get('tmdb_vote_count'),
        movie_data.get('popularity'),
        movie_data.get('content_rating'),
        movie_data.get('poster_path'),
        movie_data.get('backdrop_path'),
        movie_data.get('trailer_url'),
        json.dumps(movie_data.get('streaming_providers', {})),
        json.dumps(movie_data.get('raw_data', {})),
        True
    )
    
    result = conn.query(sql, params)
    return result[0]['movie_id'] if result else None