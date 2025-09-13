#!/usr/bin/env python3

import sqlite3

# Connect to the database
conn = sqlite3.connect('confessions.db')
cursor = conn.cursor()

# Check current posts table schema
print("Current posts table columns:")
cursor.execute('PRAGMA table_info(posts)')
posts_columns = cursor.fetchall()
for i, row in enumerate(posts_columns):
    print(f"{i+1}. {row[1]} ({row[2]})")

print(f"\nTotal columns in posts: {len(posts_columns)}")

# Check if posts_new table exists
try:
    cursor.execute('PRAGMA table_info(posts_new)')
    posts_new_columns = cursor.fetchall()
    if posts_new_columns:
        print(f"\nposts_new table exists with {len(posts_new_columns)} columns:")
        for i, row in enumerate(posts_new_columns):
            print(f"{i+1}. {row[1]} ({row[2]})")
    else:
        print("\nposts_new table does not exist")
except:
    print("\nposts_new table does not exist")

# Check sample data structure
print("\nSample posts data:")
cursor.execute('SELECT * FROM posts LIMIT 1')
sample = cursor.fetchone()
if sample:
    print(f"Sample row has {len(sample)} values: {sample}")
else:
    print("No data in posts table")

conn.close()
