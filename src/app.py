from flask import Flask, request, jsonify, render_template

from search import init_search_module
from search.search_module import perform_search

from cache import init_cache_module, store_results, get_results

from llm.llm_module import init_llm, generate_ai_response
from document_processor import init_processor
from config.config import DOCS_FOLDER
import json

from autocomplete import init_autocomplete, get_autocomplete_suggestions, update_click_count

app = Flask(__name__)

all_titles = []

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '')
    aggregation_method = request.args.get('aggregationMethod', 'single')
    syntactic_methods = json.loads(request.args.get('syntacticMethods', '[]'))
    semantic_methods = json.loads(request.args.get('semanticMethods', '[]'))
    options = json.loads(request.args.get('options', '[]'))

    if not query:
        return jsonify({"error": "No query provided"}), 400

    update_click_count(query)

    search_methods = syntactic_methods + semantic_methods

    if 'caching' in options:
        cached_results = get_results(query, aggregation_method, search_methods, options)
        if cached_results:
            return jsonify(cached_results)

    results = perform_search(query, aggregation_method, syntactic_methods, semantic_methods)
    
    ai_response = None
    if 'ai_assist' in options:
        ai_response = generate_ai_response(query, results[:3])
    
    response = {
        "search_results": results[:10],
        "ai_response": ai_response.get('full_content', '') if ai_response else None
    }

    if 'caching' in options:
        store_results(query, aggregation_method, search_methods, options, results, response.get('ai_response'))
    
    return jsonify(response)

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

    print("\nInitializing documents", flush=True)
    indexed_count, documents = init_processor()

    print("\nInitializing search module", flush=True)
    init_search_module(documents)

    print("\nInitializing cache module", flush=True)
    init_cache_module()

    print("\nInitializing autocomplete module", flush=True)
    init_autocomplete(documents, indexed_count)

    print("\nInitializing LLM module", flush=True)
    init_llm()

    app.run(debug=True, host='0.0.0.0')
