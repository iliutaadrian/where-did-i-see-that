# app.py
from flask import Flask
from flask_cors import CORS
from search_routes import search_bp
from youtube_routes import youtube_bp
from search import init_search_module
from cache import init_cache_module
from llm.llm_module import init_llm
from autocomplete import init_autocomplete
from index import init_db, add_video, add_transcript_segments, search_transcripts
import os

def create_app():
    app = Flask(__name__)
    
    # Configure CORS
    CORS(app, resources={
        r"/youtube/*": {
            "origins": ["http://localhost:3000"],
            "methods": ["GET", "POST", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type"]
        },
        r"/search/*": {
            "origins": ["http://localhost:3000"],
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type"]
        }
    })

    # Register blueprints
    app.register_blueprint(search_bp, url_prefix='/search')
    app.register_blueprint(youtube_bp, url_prefix='/youtube')

    # Initialize database
    print("\nInitializing database...", flush=True)
    init_db()
    print("Database initialization complete!", flush=True)

    return app

app = create_app()

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,DELETE,OPTIONS')
    return response

if __name__ == '__main__':
    # Ensure data directory exists
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    # Initialize all modules
    print("\nInitializing modules...", flush=True)
    
    # Initialize database first
    print("\nInitializing database...", flush=True)
    init_db()
    
    # Initialize other modules if needed
    # print("\nInitializing search module", flush=True)
    # init_search_module(documents)
    # print("\nInitializing cache module", flush=True)
    # init_cache_module()
    # print("\nInitializing autocomplete module", flush=True)
    # init_autocomplete(documents, 0)
    # print("\nInitializing LLM module", flush=True)
    # init_llm()
    
    print("\nAll modules initialized!", flush=True)
    app.run(debug=True, host='0.0.0.0')
