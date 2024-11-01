# routes/youtube_routes.py
from flask import Blueprint, request, jsonify
from index import youtube_service

youtube_bp = Blueprint('youtube', __name__)

@youtube_bp.route('/channels', methods=['GET'])
def get_channels():
    try:
        videos = youtube_service.get_indexed_channels()
        return jsonify({"videos": videos})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@youtube_bp.route('/channels', methods=['POST'])
def add_channel():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    
    try:
        result = youtube_service.add_channel(url)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@youtube_bp.route('/channels/<channel_id>', methods=['DELETE'])
def remove_channel(channel_id):
    try:
        success = youtube_service.remove_channel(channel_id)
        if success:
            return jsonify({"message": "Channel removed successfully"})
        return jsonify({"error": "Channel not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@youtube_bp.route('/reindex', methods=['POST'])
def reindex_channels():
    try:
        result = youtube_service.reindex_all_channels()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
