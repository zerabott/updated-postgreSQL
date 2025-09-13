#!/usr/bin/env python3
"""
Manual migration script to add rejection reason columns to PostgreSQL
"""
import os
import sys
from db_connection import get_db_connection

def apply_rejection_migration():
    """Apply the rejection reason migration to PostgreSQL"""
    print("🔄 Applying rejection reason migration to PostgreSQL...")
    
    try:
        db_conn = get_db_connection()
        with db_conn.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if columns already exist
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'posts' 
                AND column_name IN ('rejection_reason', 'rejected_by_admin', 'rejection_timestamp')
            """)
            existing_columns = [row[0] for row in cursor.fetchall()]
            print(f"📋 Existing rejection columns: {existing_columns}")
            
            # Add rejection_reason column if it doesn't exist
            if 'rejection_reason' not in existing_columns:
                print("➕ Adding rejection_reason column...")
                cursor.execute("ALTER TABLE posts ADD COLUMN rejection_reason TEXT")
                print("✅ Added rejection_reason column")
            else:
                print("✅ rejection_reason column already exists")
            
            # Add rejected_by_admin column if it doesn't exist
            if 'rejected_by_admin' not in existing_columns:
                print("➕ Adding rejected_by_admin column...")
                cursor.execute("ALTER TABLE posts ADD COLUMN rejected_by_admin INTEGER")
                print("✅ Added rejected_by_admin column")
            else:
                print("✅ rejected_by_admin column already exists")
            
            # Add rejection_timestamp column if it doesn't exist
            if 'rejection_timestamp' not in existing_columns:
                print("➕ Adding rejection_timestamp column...")
                cursor.execute("ALTER TABLE posts ADD COLUMN rejection_timestamp TIMESTAMP")
                print("✅ Added rejection_timestamp column")
            else:
                print("✅ rejection_timestamp column already exists")
            
            # Create index for rejected posts if it doesn't exist
            try:
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_rejected ON posts (rejected_by_admin, rejection_timestamp) WHERE rejected_by_admin IS NOT NULL")
                print("✅ Created index for rejected posts")
            except Exception as e:
                print(f"⚠️  Index creation warning: {e}")
            
            # Commit the changes
            conn.commit()
            print("🎉 Migration completed successfully!")
            
            # Verify the columns were added
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'posts' 
                AND column_name IN ('rejection_reason', 'rejected_by_admin', 'rejection_timestamp')
                ORDER BY column_name
            """)
            final_columns = cursor.fetchall()
            print(f"📋 Final rejection columns: {final_columns}")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Starting PostgreSQL rejection migration...")
    success = apply_rejection_migration()
    if success:
        print("✅ Migration completed successfully!")
        sys.exit(0)
    else:
        print("❌ Migration failed!")
        sys.exit(1)
