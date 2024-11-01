import os
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize
from config.config import DATA_FOLDER
import re
import faiss
from scipy.sparse import csr_matrix

from search.syntactic_helper import clear_text, find_snippet, highlight_terms

documents = None
tfidf_vectorizer = None
faiss_index = None
document_paths = None
document_names = None
FAISS_INDEX_PATH = os.path.join(DATA_FOLDER, "faiss_bm25_index")

# BM25 parameters
k1 = 1.5
b = 0.75

def init(docs):
    global documents, tfidf_vectorizer, faiss_index, document_paths, document_names
    documents = docs 
    document_paths = [doc['path'] for doc in docs]
    document_names = [doc['name'] for doc in docs]
    
    # Use the pre-processed content directly
    processed_docs = [f"{doc['name']} {doc['content']}" for doc in docs]
    
    # Use TfidfVectorizer with custom parameters
    tfidf_vectorizer = TfidfVectorizer(lowercase=False, tokenizer=lambda x: x.split(), use_idf=True, smooth_idf=False, sublinear_tf=False)
    tfidf_matrix = tfidf_vectorizer.fit_transform(processed_docs)
    
    # Extract term frequencies and document frequencies
    term_freq = tfidf_matrix.copy()
    term_freq.data = np.ones_like(term_freq.data)  # Set all non-zero elements to 1
    term_freq = term_freq.multiply(tfidf_matrix)  # Element-wise multiplication to get term frequencies
    
    doc_freq = np.bincount(tfidf_matrix.indices, minlength=tfidf_matrix.shape[1])
    
    # Calculate document lengths and average document length
    doc_lengths = term_freq.sum(axis=1).A1
    avg_doc_length = np.mean(doc_lengths)
    
    # Calculate IDF
    N = len(processed_docs)
    idf = np.log((N - doc_freq + 0.5) / (doc_freq + 0.5))
    
    # Calculate BM25 scores
    bm25_scores = []
    for i in range(N):
        doc_tf = term_freq[i].toarray().flatten()
        numerator = doc_tf * (k1 + 1)
        denominator = doc_tf + k1 * (1 - b + b * doc_lengths[i] / avg_doc_length)
        bm25_scores.append(idf * numerator / denominator)
    
    bm25_matrix = np.vstack(bm25_scores)
    
    # Normalize BM25 scores
    bm25_matrix_normalized = normalize(bm25_matrix, norm='l2', axis=1)
    
    # Create and train the FAISS index
    dimension = bm25_matrix_normalized.shape[1]
    faiss_index = faiss.IndexFlatIP(dimension)  # Inner Product Index
    faiss_index.add(bm25_matrix_normalized.astype('float32'))
    
    # Save the FAISS index
    faiss.write_index(faiss_index, FAISS_INDEX_PATH)
    
    print(f"BM25 FAISS search initialized with {len(documents)} documents.")

def search(query, k=5):
    if faiss_index is None or tfidf_vectorizer is None:
        raise ValueError("BM25 FAISS search not initialized. Call init() first.")
    
    # Process the query in the same way as the documents
    processed_query = clear_text(query)
    
    # Transform query to TF-IDF vector
    query_vec = tfidf_vectorizer.transform([processed_query])
    
    # Convert to BM25 vector
    query_tf = query_vec.copy()
    query_tf.data = np.ones_like(query_tf.data)  # Set all non-zero elements to 1
    query_tf = query_tf.multiply(query_vec)  # Element-wise multiplication to get term frequencies
    
    N = len(documents)
    doc_freq = np.bincount(query_vec.indices, minlength=query_vec.shape[1])
    idf = np.log((N - doc_freq + 0.5) / (doc_freq + 0.5))
    
    query_tf = query_tf.toarray().flatten()
    numerator = query_tf * (k1 + 1)
    denominator = query_tf + k1
    query_bm25 = idf * numerator / denominator
    
    query_bm25_normalized = normalize(query_bm25.reshape(1, -1), norm='l2')
    
    # Perform the search
    scores, indices = faiss_index.search(query_bm25_normalized.astype('float32'), k)
    
    results = []
    for i, idx in enumerate(indices[0]):
        doc = documents[idx]
        content = doc['content']
        original_content = doc['original_content']
        content_length = len(original_content)
        
        content_snippet = find_snippet(content, query)
        
        highlighted_content = highlight_terms(original_content, query)
        highlighted_name = highlight_terms(doc['name'], query)
        
        relevance_score = float(scores[0][i])
        
        results.append({
            "path": doc['path'],
            "highlighted_name": highlighted_name,
            "content_snippet": content_snippet,
            "content": content,
            "original_content": original_content,
            "highlighted_content": highlighted_content,
            "content_length": content_length,
            "relevance_score": relevance_score,
        })
    
    return results


