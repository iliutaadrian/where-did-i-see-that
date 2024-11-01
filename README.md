<h2 align="center">
DOCU-SEEK PLAYGROUND
</h2>

<p align="center">
	<img src="https://img.shields.io/github/license/iliutaadrian/docu-seek?style=flat&logo=opensourceinitiative&logoColor=white&color=0080ff" alt="license">
	<img src="https://img.shields.io/github/last-commit/iliutaadrian/docu-seek?style=flat&logo=git&logoColor=white&color=0080ff" alt="last-commit">
	<img src="https://img.shields.io/github/languages/top/iliutaadrian/docu-seek?style=flat&color=0080ff" alt="repo-top-language">
	<img src="https://img.shields.io/github/languages/count/iliutaadrian/docu-seek?style=flat&color=0080ff" alt="repo-language-count">
</p>

<p align="center">
	<img src="https://img.shields.io/badge/JavaScript-F7DF1E.svg?style=flat&logo=JavaScript&logoColor=black" alt="JavaScript">
	<img src="https://img.shields.io/badge/scikitlearn-F7931E.svg?style=flat&logo=scikit-learn&logoColor=white" alt="scikitlearn">
	<img src="https://img.shields.io/badge/HTML5-E34F26.svg?style=flat&logo=HTML5&logoColor=white" alt="HTML5">
	<img src="https://img.shields.io/badge/YAML-CB171E.svg?style=flat&logo=YAML&logoColor=white" alt="YAML">
	<img src="https://img.shields.io/badge/Python-3776AB.svg?style=flat&logo=Python&logoColor=white" alt="Python">
	<br>
	<img src="https://img.shields.io/badge/Docker-2496ED.svg?style=flat&logo=Docker&logoColor=white" alt="Docker">
	<img src="https://img.shields.io/badge/NumPy-013243.svg?style=flat&logo=NumPy&logoColor=white" alt="NumPy">
	<img src="https://img.shields.io/badge/Flask-000000.svg?style=flat&logo=Flask&logoColor=white" alt="Flask">
	<img src="https://img.shields.io/badge/Markdown-000000.svg?style=flat&logo=Markdown&logoColor=white" alt="Markdown">
</p>

## 📍 Overview

Docu-Seek is a document search platform designed for efficient use in personal or organizational document collections. It makes it easy to visualize and compare different types of search algorithms, from basic text matching to advanced AI-powered semantic search.

![Screenshot 2024-10-31 at 15 33 33](https://github.com/user-attachments/assets/538fc6a6-1ada-4c1f-9ed7-2e1f4c860f2a)


## 🔍 Search Methods

### Syntactic Search Methods
- **Full-Text Search (FTS)**: Quick word-based search using an index. Good for exact matches.
- **BM25**: Ranks documents by relevance to a search query.
- **TF-IDF**: Finds important words in documents for similarity matching.

### Semantic Search Methods
- **OpenAI Embeddings**: Uses AI to understand context and meaning in searches.
- **MiniLM L6 v2**: Fast, lightweight semantic search model.
- **MPNet Base v2**: High-performance semantic search model.
- **BGE Base**: Bilingual optimized embeddings (Chinese/English).

### Search Aggregation Methods
- **Single Search**: Default method combining multiple techniques.
- **Linear Combination**: Combines scores using weighted averages.
- **Reciprocal Rank Fusion**: Combines rankings from multiple methods.
- **Cascade Search**: Sequential filtering using multiple methods.

### Additional Features
- **Popularity Ranking**: Result ranking based on user behavior
- **Query Caching**: Performance optimization through caching
- **AI-Assisted Search**: AI analysis and result summarization
- **Autocomplete**: Smart suggestions using TF-IDF and user queries

## 📂 Repository Structure

```sh
└── docu-seek/
    ├── Dockerfile
    ├── README.md
    ├── docker-compose.yml
    ├── docs/
    ├── requirements.txt
    ├── src
    │   ├── app.py
    │   ├── config/
    │   ├── document_processor.py
    │   ├── llm.py
    │   ├── search/
    │   └── templates/
    └── test/
```

## 🚀 Getting Started

### Prerequisites
- Docker (recommended)
- Python 3.7+ (for local development)

### Quick Start

1. Clone the repository:
```sh
git clone https://github.com/iliutaadrian/docu-seek
cd docu-seek
```

2. Set up environment:
```sh
cp .env.example .env
# Edit .env with your OpenAI API key
```

3. Run with Docker:
```sh
docker compose up
```

You'll see output like this as the system initializes:
```
web-1  | Skipping unchanged file: /app/docs/tm.wiki/Product-version-setup.md
web-1  | Skipping unchanged file: /app/docs/tm.wiki/Upgrade-RPush-Certificates.md
...
web-1  | Fetched 250 documents from the database

web-1  | Initializing search module
web-1  | TF-IDF FAISS search initialized with 250 documents.
web-1  | BM25 FAISS search initialized with 250 documents.
web-1  | OpenAI embeddings FAISS search initialized with 250 documents.
web-1  | Loaded existing FAISS index with 1294 vectors
web-1  | all-MiniLM-L6-v2 embeddings FAISS search initialized with 250 documents.
web-1  | all-mpnet-base-v2 embeddings FAISS search initialized with 250 documents.
web-1  | BAAI/bge-base-en-v1.5 embeddings FAISS search initialized with 250 documents.
```

4. Access the interface at `http://localhost:5017`

## 🧪 Testing

For load testing:
```sh
k6 run test/k6_search_load_test.js
```

## 📄 License

This project is licensed under the [MIT License](LICENSE).
