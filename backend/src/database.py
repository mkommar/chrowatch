import sqlite3
import json
import numpy as np
import os

DATABASE_PATH = 'videos.db'

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = dict_factory
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Check if the videos table exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='videos'")
    table_exists = c.fetchone()
    
    if table_exists:
        # If the table exists, check if the filepath column exists
        c.execute("PRAGMA table_info(videos)")
        columns = [column['name'] for column in c.fetchall()]
        
        if 'filepath' not in columns:
            # Add the filepath column if it doesn't exist
            c.execute("ALTER TABLE videos ADD COLUMN filepath TEXT")
    else:
        # If the table doesn't exist, create it with all necessary columns
        c.execute('''CREATE TABLE videos
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      filename TEXT NOT NULL,
                      filepath TEXT NOT NULL,
                      embedding TEXT)''')
    
    conn.commit()
    conn.close()

def insert_video(filename, filepath):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO videos (filename, filepath) VALUES (?, ?)",
              (filename, filepath))
    video_id = c.lastrowid
    conn.commit()
    conn.close()
    return video_id

def update_video_embedding(video_id, embedding):
    conn = get_db_connection()
    c = conn.cursor()
    embedding_json = json.dumps(embedding.flatten().tolist())
    c.execute("UPDATE videos SET embedding = ? WHERE id = ?",
              (embedding_json, video_id))
    conn.commit()
    conn.close()

def get_all_videos():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM videos")
    videos = c.fetchall()
    conn.close()
    
    for video in videos:
        if video['embedding']:
            video['embedding'] = np.array(json.loads(video['embedding'])).reshape(1, -1)
    
    return videos

def get_video_by_id(video_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM videos WHERE id = ?", (video_id,))
    video = c.fetchone()
    conn.close()
    
    if video and video['embedding']:
        video['embedding'] = np.array(json.loads(video['embedding']))
    
    return video

def get_vectorized_videos():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM videos WHERE embedding IS NOT NULL")
    videos = c.fetchall()
    conn.close()
    
    for video in videos:
        video['embedding'] = np.array(json.loads(video['embedding']))
    
    return videos

# Initialize the database when this module is imported
init_db()