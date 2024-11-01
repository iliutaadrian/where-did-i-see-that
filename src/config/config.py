import os

# Get the absolute path to the project root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# Define paths relative to the project root
DATA_FOLDER = os.path.join(PROJECT_ROOT, 'data')
DOCS_FOLDER = os.path.join(PROJECT_ROOT, 'docs')

DB_PATH = os.path.join(DATA_FOLDER, 'documents.db')

# Ensure the data folder exists
os.makedirs(DATA_FOLDER, exist_ok=True)
