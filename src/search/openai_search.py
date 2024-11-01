import os
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from config.config import DATA_FOLDER
from search.syntactic_helper import find_snippet, highlight_terms
from collections import defaultdict

embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
documents = None
vector_store = None
FAISS_INDEX_PATH = os.path.join(DATA_FOLDER, "faiss_openai_index")

def init(docs):
    global documents, vector_store
    documents = docs
    
    if os.path.exists(FAISS_INDEX_PATH):
        try:
            vector_store = FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
        except Exception:
            vector_store = create_new_index(documents)
    else:
        vector_store = create_new_index(documents)
    
    print(f"OpenAI embeddings FAISS search initialized with {len(documents)} documents.")

def create_new_index(docs):
    langchain_docs = [
        Document(page_content=doc['content'], metadata={"path": doc['path'], "name": doc['name']})
        for doc in docs
    ]
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=20,
        length_function=len,
    )
    split_docs = text_splitter.split_documents(langchain_docs)
    
    vs = FAISS.from_documents(split_docs, embeddings)
    
    vs.save_local(FAISS_INDEX_PATH)
    
    return vs

def search(query, k=5):
    if vector_store is None:
        raise ValueError("OpenAI embeddings vector store not initialized. Call init() first.")
    
    # Get more results initially to ensure we have enough unique documents
    semantic_results = vector_store.similarity_search_with_score(query, k=k*3)
    
    # Group results by document path
    doc_results = defaultdict(lambda: {'chunks': [], 'max_score': 0})
    
    for doc, score in semantic_results:
        doc_path = doc.metadata["path"]
        relevance_score = 1 - score
        
        doc_results[doc_path]['chunks'].append({
            'content': doc.page_content,
            'score': relevance_score
        })
        
        # Update max score if this chunk has a higher score
        if relevance_score > doc_results[doc_path]['max_score']:
            doc_results[doc_path]['max_score'] = relevance_score

    # Convert to final results format
    results = []
    
    for doc_path, result_data in doc_results.items():
        global_doc = next((d for d in documents if d['path'] == doc_path), None)
        
        if global_doc:
            content = global_doc['content']
            original_content = global_doc['original_content']
            content_length = len(original_content)
            
            # Sort chunks by score
            sorted_chunks = sorted(result_data['chunks'], 
                                 key=lambda x: x['score'], 
                                 reverse=True)
            
            # Get the highest scoring chunk for the snippet
            best_chunk = sorted_chunks[0]
            content_snippet = find_snippet(best_chunk['content'], query)
            
            highlighted_content = highlight_terms(original_content, query)
            highlighted_name = highlight_terms(global_doc['name'], query)
            
            result = {
                "path": doc_path,
                "highlighted_name": highlighted_name,
                "content_snippet": content_snippet,
                "content": content,
                "original_content": original_content,
                "highlighted_content": highlighted_content,
                "content_length": content_length,
                "relevance_score": result_data['max_score'],
                "chunks": [
                    {
                        "content": chunk['content'],
                        "score": chunk['score']
                    }
                    for chunk in sorted_chunks
                ]
            }
            
            results.append(result)
    
    # Sort by the maximum chunk score and return top k
    results.sort(key=lambda x: x['relevance_score'], reverse=True)
    return results[:k]
