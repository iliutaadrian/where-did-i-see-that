from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

from search import init_search_module
from search.search_module import perform_search

from cache import init_cache_module, store_results, get_results

from llm.llm_module import init_llm, generate_ai_response
from document_processor import init_processor
from config.config import DOCS_FOLDER
import json

from autocomplete import init_autocomplete, get_autocomplete_suggestions, update_click_count

app = Flask(__name__)
CORS(app)  # This enables CORS for all routes

all_titles = []

@app.route('/search', methods=['GET'])
def search():
    try:
        query = request.args.get('q', '')
        print(f"Received search query: {query}")
        
        aggregation_method = request.args.get('aggregationMethod', 'single')
        print(f"Aggregation method: {aggregation_method}")
        
        syntactic_methods = json.loads(request.args.get('syntacticMethods', '[]'))
        print(f"Syntactic methods: {syntactic_methods}")
        
        semantic_methods = json.loads(request.args.get('semanticMethods', '[]'))
        print(f"Semantic methods: {semantic_methods}")
        
        options = json.loads(request.args.get('options', '[]'))
        print(f"Options: {options}")

        if not query:
            return jsonify({"error": "No query provided"}), 400

        print("Performing search...")
        results = perform_search(query, aggregation_method, syntactic_methods, semantic_methods)
        print(f"Search results: {results}")
        
        if results is None:
            print("No results found")
            return jsonify({
                "search_results": [],
                "error": "Search failed - no results found"
            })

        return jsonify({
            "search_results": results[:10],
            "total_results": len(results)
        })

    except Exception as e:
        print(f"Search error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    suggestions = get_autocomplete_suggestions(query)
    return jsonify(suggestions)

@app.route('/update_click_count', methods=['POST'])
def update_click():
    data = request.json
    phrase = data.get('phrase')
    if not phrase:
        return jsonify({"error": "No phrase provided"}), 400
    
    update_click_count(phrase)
    return jsonify({"success": True, "message": "Click count updated"})

if __name__ == '__main__':
    documents = [
        {
            "path": "sample1.txt",
            "name": "Sample Document 1",
            "content": "This is a sample document for testing search functionality.",
            "original_content": "This is a sample document for testing search functionality."
        },
        {
            "path": "sample2.txt",
            "name": "Sample Document 2",
            "content": "Another sample document with different content.",
            "original_content": "Another sample document with different content."
        }
    ]

    print("\nInitializing search module", flush=True)
    init_search_module(documents)

    print("\nInitializing cache module", flush=True)
    init_cache_module()

    print("\nInitializing autocomplete module", flush=True)
    init_autocomplete(documents, 0)

    print("\nInitializing LLM module", flush=True)
    init_llm()

    app.run(debug=True, host='0.0.0.0')
