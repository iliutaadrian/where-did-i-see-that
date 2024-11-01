import sqlite3
import os
from typing import List, Dict
from config.config import DATA_FOLDER


DB_PATH = os.path.join(DATA_FOLDER, 'youtube.db')

def get_connection() -> sqlite3.Connection:
    """Create a database connection with proper settings"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db():
    """Initialize the database schema"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS videos (
            video_id PRIMARY KEY,
            title,
            url,
            published_at,
            created_at DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS transcripts (
            transcript_id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id,
            start_time,
            stop_time,
            text,
            created_at DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (video_id) REFERENCES videos(video_id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_transcripts_video ON transcripts(video_id);
        CREATE INDEX IF NOT EXISTS idx_videos_published ON videos(published_at);
        
        CREATE VIRTUAL TABLE IF NOT EXISTS transcripts_fts USING fts5(
            transcript_id UNINDEXED,
            video_id UNINDEXED,
            text,
            content='transcripts',
            content_rowid='transcript_id'
        );

        CREATE TRIGGER IF NOT EXISTS transcripts_ai AFTER INSERT ON transcripts BEGIN
            INSERT INTO transcripts_fts(transcript_id, video_id, text)
            VALUES (new.transcript_id, new.video_id, new.text);
        END;

        CREATE TRIGGER IF NOT EXISTS transcripts_ad AFTER DELETE ON transcripts BEGIN
            INSERT INTO transcripts_fts(transcripts_fts, rowid, transcript_id, video_id, text)
            VALUES('delete', old.transcript_id, old.transcript_id, old.video_id, old.text);
        END;

        CREATE TRIGGER IF NOT EXISTS transcripts_au AFTER UPDATE ON transcripts BEGIN
            INSERT INTO transcripts_fts(transcripts_fts, rowid, transcript_id, video_id, text)
            VALUES('delete', old.transcript_id, old.transcript_id, old.video_id, old.text);
            INSERT INTO transcripts_fts(transcript_id, video_id, text)
            VALUES (new.transcript_id, new.video_id, new.text);
        END;
    ''')

    conn.commit()
    conn.close()

def add_video(video_data: Dict) -> None:
    """Add or update a video"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR REPLACE INTO videos (
            video_id, title, url, published_at
        ) VALUES (?, ?, ?, ?)
    ''', (
        video_data['video_id'],
        video_data['title'],
        video_data['url'],
        video_data.get('published_at')
    ))

    conn.commit()
    conn.close()

def add_transcript_segments(video_id: str, segments: List[Dict]) -> None:
    """Add transcript segments for a video"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executemany('''
        INSERT INTO transcripts (
            video_id, start_time, stop_time, text
        ) VALUES (?, ?, ?, ?)
    ''', [
        (video_id, segment['start'], segment['end'], segment['text'])
        for segment in segments
    ])

    conn.commit()
    conn.close()

def search_transcripts(query: str, limit: int = 10) -> List[Dict]:
    """Search through video transcripts"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        WITH ranked_segments AS (
            SELECT 
                t.transcript_id,
                t.video_id,
                t.start_time,
                t.stop_time,
                t.text,
                v.title as video_title,
                v.url as video_url,
                rank
            FROM transcripts_fts fts
            JOIN transcripts t ON fts.rowid = t.transcript_id
            JOIN videos v ON t.video_id = v.video_id
            WHERE transcripts_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        )
        SELECT * FROM ranked_segments
    ''', (query, limit))

    results = []
    for row in cursor.fetchall():
        results.append({
            'transcript_id': row[0],
            'video_id': row[1],
            'start_time': row[2],
            'stop_time': row[3],
            'text': row[4],
            'video_title': row[5],
            'video_url': row[6],
            'rank': row[7]
        })

    conn.close()
    return results

def get_video_transcript(video_id: str) -> List[Dict]:
    """Get all transcript segments for a video"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT start_time, stop_time, text
        FROM transcripts
        WHERE video_id = ?
        ORDER BY start_time
    ''', (video_id,))

    segments = []
    for row in cursor.fetchall():
        segments.append({
            'start': row[0],
            'end': row[1],
            'text': row[2]
        })

    conn.close()
    return segments

def delete_video(video_id: str) -> bool:
    """Delete a video and its transcripts"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM videos WHERE video_id = ?', (video_id,))
    deleted = cursor.rowcount > 0

    conn.commit()
    conn.close()
    return deleted
