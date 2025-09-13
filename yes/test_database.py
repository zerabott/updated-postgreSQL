#!/usr/bin/env python3
"""
Database Connection Test Script

Run this script to test your database connection and setup.
"""

import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_connection():
    """Test database connection and basic operations"""
    try:
        logger.info("🔍 Testing database connection...")
        
        # Import database modules
        from db_connection import get_db_connection, execute_query
        from migration import run_database_migrations
        
        # Get database connection
        db_conn = get_db_connection()
        logger.info(f"✅ Database connection initialized")
        logger.info(f"📊 Using PostgreSQL: {db_conn.use_postgresql}")
        
        if db_conn.use_postgresql:
            logger.info("🐘 PostgreSQL mode detected")
        else:
            logger.info("🗄️ SQLite mode detected")
        
        # Test basic query
        logger.info("🧪 Testing basic query...")
        result = execute_query("SELECT 1 as test", fetch='one')
        logger.info(f"✅ Basic query successful: {result}")
        
        # Run migrations
        logger.info("🔄 Running database migrations...")
        run_database_migrations()
        logger.info("✅ Migrations completed successfully")
        
        # Test table creation
        logger.info("🔍 Checking if tables exist...")
        if db_conn.use_postgresql:
            tables_query = """
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """
        else:
            tables_query = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        
        tables = execute_query(tables_query, fetch='all')
        if tables:
            logger.info("✅ Found tables:")
            for table in tables:
                table_name = table[0] if isinstance(table, tuple) else table['table_name'] if db_conn.use_postgresql else table['name']
                logger.info(f"  📋 {table_name}")
        else:
            logger.warning("⚠️ No tables found")
        
        # Test insert and select
        logger.info("🧪 Testing user creation...")
        test_user_id = 999999999
        
        # Insert test user
        if db_conn.use_postgresql:
            insert_query = "INSERT INTO users (user_id, username, first_name) VALUES (%s, %s, %s) ON CONFLICT (user_id) DO NOTHING"
        else:
            insert_query = "INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)"
        
        execute_query(insert_query, (test_user_id, "test_user", "Test User"))
        logger.info("✅ Test user inserted")
        
        # Select test user
        select_query = f"SELECT user_id, username, first_name FROM users WHERE user_id = {db_conn.get_placeholder()}"
        user = execute_query(select_query, (test_user_id,), fetch='one')
        
        if user:
            user_id = user[0] if isinstance(user, tuple) else user['user_id']
            username = user[1] if isinstance(user, tuple) else user['username']
            first_name = user[2] if isinstance(user, tuple) else user['first_name']
            logger.info(f"✅ Test user found: ID={user_id}, username={username}, name={first_name}")
        else:
            logger.error("❌ Test user not found")
            return False
        
        # Clean up test user
        delete_query = f"DELETE FROM users WHERE user_id = {db_conn.get_placeholder()}"
        execute_query(delete_query, (test_user_id,))
        logger.info("🧹 Test user cleaned up")
        
        logger.info("🎉 All database tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_database_info():
    """Show current database configuration"""
    logger.info("📋 Database Configuration:")
    
    # Import config
    from config import (
        DATABASE_URL, USE_POSTGRESQL, DB_PATH,
        PG_HOST, PG_PORT, PG_DATABASE, PG_USER
    )
    
    logger.info(f"  USE_POSTGRESQL: {USE_POSTGRESQL}")
    
    if DATABASE_URL:
        # Mask password in URL for logging
        masked_url = DATABASE_URL
        if '@' in masked_url:
            parts = masked_url.split('@')
            if ':' in parts[0]:
                user_pass = parts[0].split(':')
                if len(user_pass) >= 2:
                    masked_url = f"{user_pass[0]}:***@{parts[1]}"
        logger.info(f"  DATABASE_URL: {masked_url}")
    
    if USE_POSTGRESQL:
        logger.info(f"  PGHOST: {PG_HOST}")
        logger.info(f"  PGPORT: {PG_PORT}")
        logger.info(f"  PGDATABASE: {PG_DATABASE}")
        logger.info(f"  PGUSER: {PG_USER}")
        logger.info(f"  PGPASSWORD: {'***' if os.getenv('PGPASSWORD') else 'Not set'}")
    else:
        logger.info(f"  DB_PATH: {DB_PATH}")

def main():
    """Main test function"""
    logger.info("🚀 Starting database connection test...")
    
    # Show configuration
    show_database_info()
    
    # Test connection
    success = test_database_connection()
    
    if success:
        logger.info("✅ Database connection test completed successfully!")
        logger.info("🎯 Your bot should work correctly with this database setup.")
        return 0
    else:
        logger.error("❌ Database connection test failed!")
        logger.error("🔧 Please check your configuration and try again.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
