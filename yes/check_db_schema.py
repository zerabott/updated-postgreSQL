#!/usr/bin/env python3
"""
Script to check database schema and migration status
"""

import sqlite3
import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import DB_PATH

def check_table_exists(cursor, table_name):
    """Check if a table exists in the database"""
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name=?
    """, (table_name,))
    return cursor.fetchone() is not None

def get_table_schema(cursor, table_name):
    """Get the schema of a table"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    return columns

def check_migrations_status(cursor):
    """Check which migrations have been applied"""
    if not check_table_exists(cursor, 'migrations'):
        return "Migrations table does not exist"
    
    cursor.execute("SELECT version, name, applied_at FROM migrations ORDER BY version")
    migrations = cursor.fetchall()
    return migrations

def main():
    print(f"Checking database: {DB_PATH}")
    print("=" * 50)
    
    if not os.path.exists(DB_PATH):
        print(f"Database file does not exist: {DB_PATH}")
        return
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Check all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [row[0] for row in cursor.fetchall()]
            
            print("EXISTING TABLES:")
            print("-" * 20)
            for table in tables:
                print(f"  ✓ {table}")
            print()
            
            # Check ranking system tables specifically
            ranking_tables = ['user_rankings', 'point_transactions', 'rank_definitions', 'user_achievements']
            print("RANKING SYSTEM TABLES:")
            print("-" * 25)
            for table in ranking_tables:
                if check_table_exists(cursor, table):
                    print(f"  ✓ {table} - EXISTS")
                    # Show schema
                    schema = get_table_schema(cursor, table)
                    for col in schema:
                        print(f"    - {col[1]} ({col[2]})")
                else:
                    print(f"  ✗ {table} - MISSING")
            print()
            
            # Check migrations status
            print("MIGRATIONS STATUS:")
            print("-" * 20)
            migrations_status = check_migrations_status(cursor)
            if isinstance(migrations_status, str):
                print(f"  {migrations_status}")
            else:
                for version, name, applied_at in migrations_status:
                    print(f"  ✓ v{version}: {name} (applied: {applied_at})")
            print()
            
            # Check posts table schema specifically
            if check_table_exists(cursor, 'posts'):
                print("POSTS TABLE SCHEMA:")
                print("-" * 20)
                schema = get_table_schema(cursor, 'posts')
                for col in schema:
                    print(f"  {col[1]} ({col[2]}) - {col[5] if col[5] else 'no default'}")
                print()

    except Exception as e:
        print(f"Error checking database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
