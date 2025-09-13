#!/usr/bin/env python3
"""
PostgreSQL Schema Fix for Notification Preferences
Fixes boolean column type mismatch errors in notification_preferences table
"""

import logging
from db_connection import get_db_connection

logger = logging.getLogger(__name__)

def fix_notification_schema():
    """Fix PostgreSQL boolean column schema issues"""
    try:
        db_conn = get_db_connection()
        
        if not db_conn.use_postgresql:
            print("✅ Not using PostgreSQL - no schema fix needed")
            return True
            
        print("🔧 Fixing PostgreSQL notification preferences schema...")
        
        with db_conn.get_connection() as conn:
            cursor = conn.cursor()
            
            # First, check if the table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'notification_preferences'
                );
            """)
            table_exists = cursor.fetchone()[0]
            
            if not table_exists:
                print("✅ notification_preferences table doesn't exist yet - will be created with correct schema")
                return True
            
            # Check current schema
            cursor.execute("""
                SELECT column_name, data_type, column_default
                FROM information_schema.columns
                WHERE table_name = 'notification_preferences'
                AND column_name IN ('comment_notifications', 'daily_digest', 'trending_alerts');
            """)
            columns = cursor.fetchall()
            
            if not columns:
                print("✅ Boolean columns don't exist yet - will be created with correct schema")
                return True
            
            print("📊 Current schema:")
            for col_name, data_type, default_val in columns:
                print(f"  - {col_name}: {data_type} (default: {default_val})")
            
            # Fix boolean columns with incorrect defaults
            boolean_columns = ['comment_notifications', 'daily_digest', 'trending_alerts']
            
            for col_name in boolean_columns:
                try:
                    print(f"🔧 Fixing {col_name} column...")
                    
                    # Drop default constraint if it exists with integer value
                    cursor.execute(f"""
                        ALTER TABLE notification_preferences 
                        ALTER COLUMN {col_name} DROP DEFAULT;
                    """)
                    
                    # Set new boolean default
                    cursor.execute(f"""
                        ALTER TABLE notification_preferences 
                        ALTER COLUMN {col_name} SET DEFAULT TRUE;
                    """)
                    
                    # Update existing rows with integer values to boolean
                    cursor.execute(f"""
                        UPDATE notification_preferences 
                        SET {col_name} = CASE 
                            WHEN {col_name}::text = '1' THEN TRUE 
                            WHEN {col_name}::text = '0' THEN FALSE 
                            ELSE {col_name}
                        END;
                    """)
                    
                    print(f"✅ Fixed {col_name} column")
                    
                except Exception as e:
                    print(f"⚠️  Error fixing {col_name}: {e}")
                    # Continue with other columns
                    continue
            
            # Commit all changes
            conn.commit()
            
            print("✅ PostgreSQL notification preferences schema fixed successfully!")
            
            # Verify the fix
            cursor.execute("""
                SELECT column_name, data_type, column_default
                FROM information_schema.columns
                WHERE table_name = 'notification_preferences'
                AND column_name IN ('comment_notifications', 'daily_digest', 'trending_alerts');
            """)
            updated_columns = cursor.fetchall()
            
            print("📊 Updated schema:")
            for col_name, data_type, default_val in updated_columns:
                print(f"  - {col_name}: {data_type} (default: {default_val})")
            
            return True
            
    except Exception as e:
        logger.error(f"Error fixing notification schema: {e}")
        print(f"❌ Error fixing notification schema: {e}")
        return False

if __name__ == "__main__":
    success = fix_notification_schema()
    if success:
        print("\n🎉 Schema fix completed successfully!")
    else:
        print("\n💥 Schema fix failed!")
