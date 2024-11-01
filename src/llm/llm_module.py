import os
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from collections import defaultdict

llm = None

def init_llm():
    global llm
    llm = ChatOpenAI(
        model_name="gpt-3.5-turbo", 
        temperature=0.2,
        max_tokens=1000
    )

def prepare_context(search_results, max_chars=2000):
    """
    Prepare context from search results, managing chunks and character limits.
    Returns both a condensed context and relevant chunks information.
    """
    processed_docs = {}
    total_chars = 0
    best_chunks = []

    for result in search_results:
        doc_path = result['path']
        
        # Skip if we've already processed this document
        if doc_path in processed_docs:
            continue
            
        chunks = result.get('chunks', [])
        if not chunks:
            # If no chunks, treat the whole content as one chunk
            chunks = [{
                'content': result.get('content_snippet', ''),
                'score': result.get('relevance_score', 0)
            }]
        
        # Sort chunks by score and get the best ones
        sorted_chunks = sorted(chunks, key=lambda x: x['score'], reverse=True)
        
        # Take the best chunks that fit within our character limit
        for chunk in sorted_chunks:
            chunk_content = chunk['content']
            chunk_len = len(chunk_content)
            
            if total_chars + chunk_len <= max_chars:
                best_chunks.append({
                    'content': chunk_content,
                    'score': chunk['score'],
                    'doc_path': doc_path
                })
                total_chars += chunk_len
            else:
                # If the chunk is too big, try to take a portion that fits
                remaining_chars = max_chars - total_chars
                if remaining_chars > 200:  # Only take partial chunks if we can get a meaningful amount
                    truncated_content = chunk_content[:remaining_chars]
                    best_chunks.append({
                        'content': truncated_content,
                        'score': chunk['score'],
                        'doc_path': doc_path
                    })
                break
                
        processed_docs[doc_path] = True
        
        if total_chars >= max_chars:
            break
    
    # Prepare the final context string
    context_parts = []
    for i, chunk in enumerate(best_chunks, 1):
        context_parts.append(f"[Chunk {i}] (Score: {chunk['score']:.2f})\n{chunk['content']}\n")
    
    return {
        'context_string': "\n".join(context_parts),
        'best_chunks': best_chunks
    }

def generate_ai_response(query, search_results):
    if llm is None:
        init_llm()
    
    # Prepare context with chunks
    context_data = prepare_context(search_results)
    
    # Define the prompt template
    prompt_template = ChatPromptTemplate.from_template("""
    You are an AI assistant tasked with answering questions based on the provided context.
    The context consists of relevant chunks from different documents, sorted by relevance score.
    Use this information to answer the user's query comprehensively but concisely.
    
    If you cannot find the answer in the context, say "I don't have enough information to answer that question."
    
    Context:
    {context}
    
    User Query: {query}
    
    Please provide a clear and focused answer, synthesizing information from the most relevant chunks.
    
    AI Response:
    """)

    chain = LLMChain(llm=llm, prompt=prompt_template)
    response = chain.run(query=query, context=context_data['context_string'])
    
    return format_ai_response(response.strip(), context_data['best_chunks'])

def format_ai_response(ai_response, best_chunks):
    # Create a summary of the sources used
    sources_summary = []
    seen_docs = set()
    for chunk in best_chunks:
        doc_path = chunk['doc_path']
        if doc_path not in seen_docs:
            sources_summary.append({
                'path': doc_path,
                'score': chunk['score']
            })
            seen_docs.add(doc_path)

    return {
        "path": None,
        "name": "AI Response",
        "content_snippet": ai_response[:100] + "...",
        "content_length": len(ai_response),
        "full_content": ai_response,
        "highlighted_content": ai_response,
        "sources_used": sources_summary,
        "used_chunks": [
            {
                'content': chunk['content'],
                'score': chunk['score'],
                'doc_path': chunk['doc_path']
            }
            for chunk in best_chunks
        ]
    }
