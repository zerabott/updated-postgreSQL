import os
import logging
import sqlite3
from typing import Any, Dict, List, Optional, Tuple, Union
from contextlib import contextmanager

try:
    import psycopg2
    import psycopg2.extras
    from psycopg2.pool import SimpleConnectionPool
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    psycopg2 = None

from config import (
    DATABASE_URL, USE_POSTGRESQL, DB_PATH,
    PG_HOST, PG_PORT, PG_DATABASE, PG_USER, PG_PASSWORD
)

logger = logging.getLogger(__name__)

class DatabaseConnection:
    """Database connection manager supporting both SQLite and PostgreSQL"""
    
    def __init__(self):
        self.use_postgresql = USE_POSTGRESQL or DATABASE_URL is not None
        self.connection_pool = None
        
        if self.use_postgresql:
            if not PSYCOPG2_AVAILABLE:
                logger.error("PostgreSQL requested but psycopg2 not available. Falling back to SQLite.")
                self.use_postgresql = False
            else:
                self._init_postgresql()
        
        if not self.use_postgresql:
            self._init_sqlite()
    
    def _init_postgresql(self):
        """Initialize PostgreSQL connection pool"""
        try:
            if DATABASE_URL:
                # Parse DATABASE_URL for Render deployment
                connection_string = DATABASE_URL
            else:
                # Build connection string from individual components
                connection_string = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DATABASE}"
            
            # Create connection pool
            self.connection_pool = SimpleConnectionPool(
                minconn=1,
                maxconn=20,
                dsn=connection_string
            )
            
            # Test connection
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    
            logger.info("PostgreSQL connection pool initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL: {e}")
            logger.info("Falling back to SQLite")
            self.use_postgresql = False
            self._init_sqlite()
    
    def _init_sqlite(self):
        """Initialize SQLite (fallback)"""
        self.db_path = DB_PATH
        logger.info(f"Using SQLite database: {self.db_path}")
    
    @contextmanager
    def get_connection(self):
        """Get database connection with automatic cleanup"""
        if self.use_postgresql:
            conn = None
            try:
                conn = self.connection_pool.getconn()
                yield conn
            finally:
                if conn:
                    self.connection_pool.putconn(conn)
        else:
            conn = sqlite3.connect(self.db_path)
            conn.execute('PRAGMA foreign_keys = ON')
            try:
                yield conn
            finally:
                conn.close()
    
    def execute_query(self, query: str, params: Optional[Tuple] = None, fetch: str = None) -> Optional[List]:
        """
        Execute a query and optionally fetch results
        
        Args:
            query: SQL query to execute
            params: Query parameters
            fetch: 'one', 'all', or None
        
        Returns:
            Query results if fetch is specified, None otherwise
        """
        try:
            with self.get_connection() as conn:
                if self.use_postgresql:
                    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                        cursor.execute(query, params or ())
                        
                        if fetch == 'one':
                            return cursor.fetchone()
                        elif fetch == 'all':
                            return cursor.fetchall()
                        else:
                            conn.commit()
                            return cursor.rowcount
                else:
                    # SQLite
                    cursor = conn.cursor()
                    cursor.execute(query, params or ())
                    
                    if fetch == 'one':
                        return cursor.fetchone()
                    elif fetch == 'all':
                        return cursor.fetchall()
                    else:
                        conn.commit()
                        return cursor.rowcount
                        
        except Exception as e:
            logger.error(f"Database query error: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise
    
    def get_placeholder(self) -> str:
        """Get the appropriate parameter placeholder for the database type"""
        return "%s" if self.use_postgresql else "?"
    
    def adapt_query_for_db(self, sqlite_query: str) -> str:
        """
        Adapt SQLite query syntax for PostgreSQL if needed
        
        Args:
            sqlite_query: Original SQLite query
            
        Returns:
            Adapted query for current database type
        """
        if not self.use_postgresql:
            return sqlite_query
        
        # Convert SQLite syntax to PostgreSQL
        query = sqlite_query
        
        # Replace ? placeholders with %s
        placeholder_count = query.count('?')
        for i in range(placeholder_count):
            query = query.replace('?', '%s', 1)
        
        # Handle common SQLite -> PostgreSQL conversions
        replacements = {
            'AUTOINCREMENT': 'SERIAL',
            'INTEGER PRIMARY KEY AUTOINCREMENT': 'SERIAL PRIMARY KEY',
            'CURRENT_TIMESTAMP': 'NOW()',
            'PRAGMA foreign_keys = ON': '',  # Not needed in PostgreSQL
        }
        
        for sqlite_syntax, pg_syntax in replacements.items():
            query = query.replace(sqlite_syntax, pg_syntax)
        
        return query
    
    def close(self):
        """Close database connections"""
        if self.use_postgresql and self.connection_pool:
            self.connection_pool.closeall()
            logger.info("PostgreSQL connection pool closed")

# Global database connection instance
db_connection = DatabaseConnection()

def get_db_connection():
    """Get the global database connection instance"""
    return db_connection

# Convenience functions for backward compatibility
def get_db():
    """Get database connection (backward compatibility)"""
    return db_connection.get_connection()

def execute_query(query: str, params: Optional[Tuple] = None, fetch: str = None):
    """Execute query using global connection"""
    return db_connection.execute_query(query, params, fetch)

def adapt_query(query: str) -> str:
    """Adapt query for current database type"""
    return db_connection.adapt_query_for_db(query)
