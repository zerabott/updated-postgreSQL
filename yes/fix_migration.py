#!/usr/bin/env python3

import sqlite3
import os

def fix_migration():
    """Fix the migration 15 issue by properly handling the posts table schema"""
    
    # Connect to database
    conn = sqlite3.connect('confessions.db')
    cursor = conn.cursor()
    
    try:
        print("🔧 Fixing migration 15...")
        
        # Check if posts_new exists and drop it
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='posts_new'")
        if cursor.fetchone():
            print("Dropping existing posts_new table...")
            cursor.execute("DROP TABLE posts_new")
        
        # Create the new posts table with ALL existing columns
        print("Creating new posts table with proper schema...")
        cursor.execute("""
            CREATE TABLE posts_new (
                post_id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT,
                category TEXT NOT NULL,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER NOT NULL,
                approved INTEGER DEFAULT NULL,
                channel_message_id INTEGER,
                flagged INTEGER DEFAULT 0,
                likes INTEGER DEFAULT 0,
                post_number INTEGER DEFAULT NULL,
                status TEXT,
                sentiment_score REAL,
                profanity_detected INTEGER,
                spam_score REAL,
                media_type TEXT DEFAULT NULL,
                media_file_id TEXT DEFAULT NULL,
                media_file_unique_id TEXT DEFAULT NULL,
                media_caption TEXT DEFAULT NULL,
                media_file_size INTEGER DEFAULT NULL,
                media_mime_type TEXT DEFAULT NULL,
                media_duration INTEGER DEFAULT NULL,
                media_width INTEGER DEFAULT NULL,
                media_height INTEGER DEFAULT NULL,
                media_thumbnail_file_id TEXT DEFAULT NULL,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        """)
        
        # Copy data from old table to new table
        print("Copying data from old table to new table...")
        cursor.execute("INSERT INTO posts_new SELECT * FROM posts")
        
        # Drop old table
        print("Dropping old posts table...")
        cursor.execute("DROP TABLE posts")
        
        # Rename new table to posts
        print("Renaming posts_new to posts...")
        cursor.execute("ALTER TABLE posts_new RENAME TO posts")
        
        # Recreate indexes
        print("Recreating indexes...")
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_posts_approved_timestamp ON posts(approved, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_posts_category ON posts(category)",
            "CREATE INDEX IF NOT EXISTS idx_posts_user_id ON posts(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_posts_media_type ON posts(media_type)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        # Mark migration 15 as completed if not already marked
        cursor.execute("SELECT version FROM migrations WHERE version = 15")
        if not cursor.fetchone():
            from datetime import datetime
            cursor.execute("""
                INSERT INTO migrations (version, name, checksum, applied_at)
                VALUES (15, 'fix_content_null_constraint_for_media', 'fixed', ?)
            """, (datetime.now().isoformat(),))
        
        conn.commit()
        print("✅ Migration 15 fixed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing migration: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    fix_migration()
