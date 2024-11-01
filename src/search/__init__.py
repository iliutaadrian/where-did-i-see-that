from .bm25_search import init as init_bm25, search as search_bm25
from .openai_search import init as init_openai, search as search_openai

from .hybrid_search import search as hybrid_search

def init_search_module(documents):
    init_bm25(documents)
    init_openai(documents)
