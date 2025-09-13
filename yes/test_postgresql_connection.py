#!/usr/bin/env python3
"""
PostgreSQL Connection Test Script for Confession Bot
Run this script to verify your PostgreSQL connection is working correctly.
"""

import os
import sys
from datetime import datetime

def test_postgresql_connection():
    """Test PostgreSQL connection and basic operations"""
    print("🔍 Testing PostgreSQL Connection...")
    print("=" * 50)
    
    try:
        # Import required modules
        from config import DATABASE_URL, USE_POSTGRESQL, PG_HOST, PG_PORT, PG_DATABASE, PG_USER
        from db_connection import get_db_connection
        from db import init_db
        
        print("✅ Successfully imported database modules")
        
        # Check configuration
        print(f"\nConfiguration:")
        print(f"USE_POSTGRESQL: {USE_POSTGRESQL}")
        print(f"DATABASE_URL configured: {'Yes' if DATABASE_URL else 'No'}")
        if not USE_POSTGRESQL:
            print("❌ USE_POSTGRESQL is False - PostgreSQL will not be used")
            return False
            
        if not DATABASE_URL:
            print("❌ DATABASE_URL is not configured")
            print("Please set your DATABASE_URL environment variable")
            return False
            
        print(f"PG_HOST: {PG_HOST}")
        print(f"PG_PORT: {PG_PORT}")
        print(f"PG_DATABASE: {PG_DATABASE}")
        print(f"PG_USER: {PG_USER}")
        
        # Test database connection
        print(f"\n🔌 Testing Database Connection...")
        db_conn = get_db_connection()
        
        if not db_conn.use_postgresql:
            print("❌ Database connection is using SQLite, not PostgreSQL")
            return False
            
        print("✅ Database connection initialized for PostgreSQL")
        
        # Test basic connection
        with db_conn.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            print(f"✅ Successfully connected to PostgreSQL: {version}")
            
        # Test database initialization
        print(f"\n📊 Testing Database Initialization...")
        init_db()
        print("✅ Database tables initialized successfully")
        
        # Test basic operations
        print(f"\n🧪 Testing Basic Database Operations...")
        
        with db_conn.get_connection() as conn:
            cursor = conn.cursor()
            placeholder = db_conn.get_placeholder()
            
            # Test table existence
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            tables = cursor.fetchall()
            print(f"✅ Found {len(tables)} tables in database:")
            for table in tables:
                print(f"   • {table[0]}")
            
            # Test inserting a test user
            try:
                cursor.execute(f"""
                    INSERT INTO users (user_id, username, first_name, join_date)
                    VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
                    ON CONFLICT (user_id) DO UPDATE SET
                        username = EXCLUDED.username,
                        first_name = EXCLUDED.first_name
                """, (999999999, "test_user", "Test User", datetime.now()))
                
                # Test reading the user
                cursor.execute(f"""
                    SELECT user_id, username, first_name FROM users 
                    WHERE user_id = {placeholder}
                """, (999999999,))
                
                user = cursor.fetchone()
                if user:
                    print(f"✅ Successfully inserted and retrieved test user: {user[1]} ({user[0]})")
                else:
                    print("❌ Failed to retrieve test user")
                    return False
                    
                # Clean up test user
                cursor.execute(f"DELETE FROM users WHERE user_id = {placeholder}", (999999999,))
                conn.commit()
                print("✅ Test user cleaned up successfully")
                
            except Exception as e:
                print(f"❌ Error during database operations: {e}")
                return False
        
        print(f"\n🎉 All PostgreSQL tests passed successfully!")
        print("Your database is ready for deployment to Render + Aiven!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure psycopg2-binary is installed: pip install psycopg2-binary")
        return False
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        print("\nTroubleshooting steps:")
        print("1. Check your DATABASE_URL is correct")
        print("2. Verify your Aiven PostgreSQL service is running")
        print("3. Check firewall settings")
        print("4. Ensure psycopg2-binary is installed")
        return False

def main():
    """Main function"""
    print("🐘 PostgreSQL Connection Test for Confession Bot")
    print("This script will test your PostgreSQL database connection")
    print()
    
    # Check if running in the right directory
    if not os.path.exists('config.py'):
        print("❌ Error: config.py not found!")
        print("Please run this script from your project root directory")
        sys.exit(1)
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Loaded environment variables from .env file")
    except ImportError:
        print("⚠️  python-dotenv not available, using system environment variables")
    
    # Run the test
    success = test_postgresql_connection()
    
    if success:
        print("\n" + "="*50)
        print("🚀 READY FOR DEPLOYMENT!")
        print("Your PostgreSQL configuration is working correctly.")
        print("You can now deploy to Render with confidence.")
        print("="*50)
        sys.exit(0)
    else:
        print("\n" + "="*50)
        print("❌ DEPLOYMENT NOT READY")
        print("Please fix the issues above before deploying.")
        print("="*50)
        sys.exit(1)

if __name__ == "__main__":
    main()
