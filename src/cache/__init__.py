from config.config import DATA_FOLDER
from typing import List, Dict, Optional, Any
import json
import os
import sqlite3

CACHE_DB_PATH = os.path.join(DATA_FOLDER, 'cache.db')

def init_cache_module():
    create_table()

def get_db_connection():
    return sqlite3.connect(CACHE_DB_PATH)

def create_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cache (
            cache_key TEXT PRIMARY KEY,
            search_results TEXT,
            ai_response TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def generate_cache_key(query: str, aggregation_method: str, search_methods: List[str], options: List[str]) -> str:
    key_components = [
        query,
        aggregation_method,
        ','.join(sorted(search_methods)),
        ','.join(sorted(options))
    ]
    return '|'.join(key_components)

def store_results(query: str, aggregation_method: str, search_methods: List[str], options: List[str], 
                  search_results: List[Dict[str, Any]], ai_response: Optional[str] = None):
    cache_key = generate_cache_key(query, aggregation_method, search_methods, options)
    conn = get_db_connection()
    cursor = conn.cursor()
    
    serialized_results = json.dumps(search_results)
    
    cursor.execute('''
        INSERT OR REPLACE INTO cache (cache_key, search_results, ai_response)
        VALUES (?, ?, ?)
    ''', (cache_key, serialized_results, ai_response))
    conn.commit()
    conn.close()

def get_results(query: str, aggregation_method: str, search_methods: List[str], options: List[str]) -> Optional[Dict]:
    cache_key = generate_cache_key(query, aggregation_method, search_methods, options)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT search_results, ai_response FROM cache WHERE cache_key = ?', (cache_key,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return {
            'search_results': json.loads(result[0]),
            'ai_response': result[1]
        }
    return None

def clear_cache():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM cache')
    conn.commit()
    conn.close()
