import os
import sqlite3
import markdown
from PyPDF2 import PdfReader
import re
from bs4 import BeautifulSoup
from config.config import DB_PATH, DOCS_FOLDER
from docx import Document 

from search.syntactic_helper import clear_text


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE VIRTUAL TABLE IF NOT EXISTS documents USING fts5(
                 path UNINDEXED,
                 name,
                 content,
                 original_content,
                 last_modified UNINDEXED
               )''')
    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")


def extract_content(file_path):
    content = ""
    
    if file_path.endswith('.md'):
        with open(file_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
            html_content = markdown.markdown(md_content)
            soup = BeautifulSoup(html_content, 'html.parser')
            content = soup.get_text()
    
    elif file_path.endswith('.pdf'):
        with open(file_path, 'rb') as f:
            reader = PdfReader(f)
            content = ' '.join(page.extract_text() for page in reader.pages)
    
    elif file_path.endswith('.txt'):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    
    elif file_path.endswith('.html'):
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
            content = soup.get_text()
    
    elif file_path.endswith('.docx'):  
        doc = Document(file_path)
        content = ' '.join([paragraph.text for paragraph in doc.paragraphs])
    
    return content


def extract_doc_name(path):
    file_name = os.path.basename(path)
    file_name = os.path.splitext(file_name)[0]
    # rules for extracting doc name
    file_name = file_name.replace('[TMS][REPORT]', '').replace('[TMS][Report]', '')
    return file_name.strip()

def index_documents():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    indexed_count = 0
    
    for root, _, files in os.walk(DOCS_FOLDER):
        for file in files:
            if file.endswith(('.md', '.pdf', '.txt', '.html', '.docx')): 
                file_path = os.path.join(root, file)
                last_modified = os.path.getmtime(file_path)
                
                c.execute("SELECT last_modified FROM documents WHERE path = ?", (file_path,))
                result = c.fetchone()
                
                if not result or result[0] < last_modified:
                    original_content = extract_content(file_path)
                    optimized_content = clear_text(original_content)
                    name = extract_doc_name(file_path)
                    path = file_path.replace(DOCS_FOLDER, '')
                    
                    c.execute("""INSERT OR REPLACE INTO documents 
                                 (path, name, content, original_content, last_modified) 
                                 VALUES (?, ?, ?, ?, ?)""",
                              (file_path, name, optimized_content, original_content, last_modified))
                    
                    indexed_count += 1
                    print(f"Indexed: {file_path}")
                else:
                    print(f"Skipping unchanged file: {file_path}")
    
    conn.commit()
    conn.close()
    print(f"Indexed or updated {indexed_count} documents")
    return indexed_count

def get_all_documents():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT path, name, content, original_content FROM documents")
    documents = [{"path": path, "name": name, "content": opt_content, "original_content": orig_content} 
                 for path, name, opt_content, orig_content in c.fetchall()]
    conn.close()
    print(f"Fetched {len(documents)} documents from the database")
    return documents

def init_processor():
    init_db()
    indexed_count = index_documents()
    return indexed_count, get_all_documents()
