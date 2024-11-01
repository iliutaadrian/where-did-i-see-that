from search.bm25_search import init as init_bm25, search as search_bm25
from search.openai_search import init as init_openai, search as search_openai
from collections import defaultdict

METHOD_WEIGHTS = {
    'fulltext': 0.3,    
    'bm25': 0.4,       
    'openai': 0.6,      
    'tfidf': 0.15,      
    'st_1': 0.2,        
    'st_2': 0.1,        
    'st_3': 0.1,        
}

# Fusion method configurations
RANK_FUSION_K = 60  # Controls penalty for lower ranks
CASCADE_THRESHOLD = 0.65  # Minimum score to consider result good enough

def search(query, methods=[], weights=None, combination_method='linear'):
    all_results = {}
    for method in methods:
        if method == 'fulltext':
            all_results[method] = search_fulltext(query)
        elif method == 'tfidf':
            all_results[method] = search_tfidf(query)
        elif method == 'bm25':
            all_results[method] = search_bm25(query)

        elif method == 'openai':
            all_results[method] = search_openai(query)
        elif method == 'st_1':
            all_results[method] = search_st_1(query)
        elif method == 'st_2':
            all_results[method] = search_st_2(query)
        elif method == 'st_3':
            all_results[method] = search_st_3(query)

    if combination_method == 'rank_fusion':
        return rank_fusion(all_results)
    elif combination_method == 'cascade':
        return cascade_search(all_results, methods)
    elif combination_method == 'linear':
        return linear_combination(all_results)
    else:
        raise ValueError(f"Unknown combination method: {combination_method}")

def linear_combination(results):
    """
    Linear combination with hardcoded weights.
    Each result's score is weighted by:
    1. Its position in the results (higher rank = higher score)
    2. Its relevance_score from the original method
    3. The method's weight from METHOD_WEIGHTS
    """
    combined_scores = defaultdict(float)
    all_docs = {}
    
    # For logging/debugging
    score_breakdown = defaultdict(dict)
    
    for method, method_results in results.items():
        weight = METHOD_WEIGHTS.get(method, 1.0/len(results))  # Fallback to equal weights
        
        for rank, result in enumerate(method_results):
            doc_id = result['path']
            all_docs[doc_id] = result
            
            # Position score * relevance score * method weight
            position_score = len(method_results) - rank
            relevance = result['relevance_score'] / 100.0  # Normalize to 0-1
            score = position_score * relevance * weight
            
            combined_scores[doc_id] += score
            
            # Store breakdown for debugging
            score_breakdown[doc_id][method] = {
                'position_score': position_score,
                'relevance': relevance,
                'weight': weight,
                'final_contribution': score
            }
    
    # Normalize scores to 0-100 range
    max_score = max(combined_scores.values()) if combined_scores else 1
    for doc_id in combined_scores:
        combined_scores[doc_id] = (combined_scores[doc_id] / max_score) * 100
    
    sorted_results = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
    
    final_results = []
    for doc_id, combined_score in sorted_results:
        result = all_docs[doc_id].copy()
        result['relevance_score'] = int(combined_score)
        result['score_breakdown'] = score_breakdown[doc_id]  # Add breakdown for transparency
        final_results.append(result)
    
    return final_results


def rank_fusion(results):
    """
    Reciprocal Rank Fusion (RRF) with hardcoded k value.
    Each document gets a score of 1/(rank + k) from each method,
    where k reduces the impact of high rankings.
    
    A smaller k (e.g., 20) gives more weight to top results
    A larger k (e.g., 60) makes ranking more democratic
    """
    fused_scores = defaultdict(float)
    all_docs = {}
    rank_contributions = defaultdict(dict)
    
    for method, method_results in results.items():
        weight = METHOD_WEIGHTS.get(method, 1.0/len(results))
        
        for rank, result in enumerate(method_results, start=1):
            doc_id = result['path']
            all_docs[doc_id] = result
            
            # RRF score formula with method weight
            rrf_score = (1 / (rank + RANK_FUSION_K)) * weight
            fused_scores[doc_id] += rrf_score
            
            # Store contribution for debugging
            rank_contributions[doc_id][method] = {
                'rank': rank,
                'rrf_score': rrf_score,
                'weight': weight
            }
    
    # Normalize to 0-100
    max_score = max(fused_scores.values()) if fused_scores else 1
    for doc_id in fused_scores:
        fused_scores[doc_id] = (fused_scores[doc_id] / max_score) * 100
    
    sorted_results = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
    
    final_results = []
    for doc_id, fused_score in sorted_results:
        result = all_docs[doc_id].copy()
        result['relevance_score'] = int(fused_score)
        result['rank_contributions'] = rank_contributions[doc_id]
        final_results.append(result)
    
    return final_results


def cascade_search(results, methods):
    all_docs = {}
    final_results = []
    method_attempts = []
    
    for method in methods:
        method_results = results[method]
        method_weight = METHOD_WEIGHTS.get(method, 1.0/len(methods))
        
        current_method_results = []
        for result in method_results:
            doc_id = result['path']
            all_docs[doc_id] = result
            
            # Apply method weight to the score
            score = (result['relevance_score'] / 100.0) * method_weight
            
            if score >= CASCADE_THRESHOLD:
                if doc_id not in [r['path'] for r in final_results]:
                    result_copy = result.copy()
                    result_copy['method_found'] = method
                    result_copy['weighted_score'] = score
                    current_method_results.append(result_copy)
        
        method_attempts.append({
            'method': method,
            'results_found': len(current_method_results),
            'max_score': max([r['weighted_score'] for r in current_method_results]) if current_method_results else 0
        })
        
        if current_method_results:
            final_results.extend(current_method_results)
            break
    
    # If no results meet threshold, use top results from last method
    if not final_results and method_results:
        top_results = method_results[:5]
        for result in top_results:
            result_copy = result.copy()
            result_copy['method_found'] = methods[-1]
            result_copy['weighted_score'] = (result['relevance_score'] / 100.0) * METHOD_WEIGHTS.get(methods[-1], 1.0/len(methods))
            final_results.append(result_copy)
    
    # Add search attempt history
    for result in final_results:
        result['method_attempts'] = method_attempts
    
    return sorted(final_results, key=lambda x: x['relevance_score'], reverse=True)
