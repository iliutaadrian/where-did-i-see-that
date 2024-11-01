import re
from typing import List, Dict
from datetime import datetime
import yt_dlp
from index import (
    add_video,
    add_transcript_segments,
    delete_video,
    get_connection,
    init_db
)

def extract_channel_id(url: str) -> str:
    """Extract channel ID from various YouTube channel URL formats"""
    # Initialize yt-dlp with minimal config for channel extraction
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'force_generic_extractor': False
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info['channel_id']
    except Exception as e:
        raise ValueError(f"Failed to extract channel ID: {str(e)}")

def get_channel_videos(channel_url: str) -> List[Dict]:
    """Get all videos from a channel using yt-dlp"""
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'force_generic_extractor': False,
        'ignoreerrors': True,
        'no_warnings': True
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            channel_info = ydl.extract_info(channel_url, download=False)
            
            if 'entries' not in channel_info:
                raise ValueError("No videos found in channel")
            
            videos = []
            for entry in channel_info['entries']:
                if entry is None:  # Skip failed extractions
                    continue
                    
                videos.append({
                    'video_id': entry['id'],
                    'title': entry['title'],
                    'url': f"https://www.youtube.com/watch?v={entry['id']}",
                    'published_at': entry.get('upload_date')
                })
            
            return videos
    except Exception as e:
        raise Exception(f"Failed to get channel videos: {str(e)}")

def get_video_transcript(video_id: str) -> List[Dict]:
    """Get video transcript using yt-dlp"""
    ydl_opts = {
        'quiet': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['en'],
        'skip_download': True,
    }
    
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Get subtitles info
            subtitles = info.get('subtitles', {})
            auto_subtitles = info.get('automatic_captions', {})
            
            # Try manual subtitles first, then auto-generated
            if 'en' in subtitles:
                subs = subtitles['en']
            elif 'en' in auto_subtitles:
                subs = auto_subtitles['en']
            else:
                return []

            # Get the first available format (usually 'vtt')
            sub_info = next((s for s in subs if s.get('ext', '') in ['vtt', 'ttml', 'srv1']), None)
            if not sub_info:
                return []

            # Download and parse the subtitles
            segments = []
            timestamp = 0
            
            for entry in sub_info['fragments']:
                segments.append({
                    'start': entry['start'],
                    'end': entry['end'],
                    'text': entry['text'].strip()
                })
            
            return segments
    except Exception as e:
        print(f"Error getting transcript for video {video_id}: {str(e)}")
        return []

def add_channel(url: str) -> Dict:
    """Add a channel and index all its videos"""
    try:
        # Get channel videos
        videos = get_channel_videos(url)
        indexed_count = 0
        failed_count = 0
        
        # Process each video
        for video in videos:
            try:
                # Add video to database
                add_video(video)
                
                # Get and add transcript
                transcript = get_video_transcript(video['video_id'])
                if transcript:
                    add_transcript_segments(video['video_id'], transcript)
                    indexed_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                print(f"Error processing video {video['video_id']}: {str(e)}")
                failed_count += 1
                continue

        return {
            'success': True,
            'total_videos': len(videos),
            'indexed_count': indexed_count,
            'failed_count': failed_count
        }
        
    except Exception as e:
        raise Exception(f"Failed to add channel: {str(e)}")

def get_indexed_channels() -> List[Dict]:
    """Get list of indexed videos with stats"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT 
            v.video_id,
            v.title,
            v.url,
            v.published_at,
            COUNT(DISTINCT t.transcript_id) as transcripts_count
        FROM videos v
        LEFT JOIN transcripts t ON t.video_id = v.video_id
        GROUP BY v.video_id
    ''')

    videos = []
    for row in cursor.fetchall():
        videos.append({
            'video_id': row[0],
            'title': row[1],
            'url': row[2],
            'indexed_at': row[3],
            'transcripts_count': row[4]
        })

    conn.close()
    return videos

def remove_channel(channel_id: str) -> bool:
    """Remove a channel and all its indexed content"""
    return delete_video(channel_id)

def reindex_all_channels() -> Dict:
    """Reindex all videos and their transcripts"""
    videos = get_indexed_channels()
    total_indexed = 0
    total_failed = 0
    
    for video in videos:
        try:
            # Remove existing data
            delete_video(video['video_id'])
            
            # Reindex video
            new_transcript = get_video_transcript(video['video_id'])
            if new_transcript:
                add_video(video)
                add_transcript_segments(video['video_id'], new_transcript)
                total_indexed += 1
            else:
                total_failed += 1
                
        except Exception as e:
            print(f"Error reindexing video {video['video_id']}: {str(e)}")
            total_failed += 1
            continue

    return {
        'videos_processed': len(videos),
        'successfully_indexed': total_indexed,
        'failed': total_failed
    }
