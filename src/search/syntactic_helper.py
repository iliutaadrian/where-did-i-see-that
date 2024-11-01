import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.util import ngrams

nltk.download('punkt_tab')
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('omw-1.4')


def clear_text(text):
    # This function should mimic the preprocessing steps used for the documents
    # You may need to import necessary libraries (e.g., nltk) at the top of the file

    # Convert to lowercase
    text = text.lower()
    
    # Tokenize
    tokens = word_tokenize(text)
    
    # Remove stop words
    stop_words = set(stopwords.words('english'))
    tokens = [token for token in tokens if token not in stop_words]
    
    # Lemmatization
    lemmatizer = WordNetLemmatizer()
    lemmatized_tokens = [lemmatizer.lemmatize(token) for token in tokens]
    
    # Generate bigrams
    bigrams = [' '.join(bg) for bg in ngrams(lemmatized_tokens, 2)]
    
    # Combine lemmatized tokens and bigrams
    processed_text = ' '.join(lemmatized_tokens + bigrams)
    
    return processed_text

def find_snippet(text, query, snippet_length=100):
    query_terms = query.lower().split()
    text_lower = text.lower()
    
    # Find the earliest occurrence of any query term
    earliest_pos = len(text)
    for term in query_terms:
        pos = text_lower.find(term)
        if pos != -1 and pos < earliest_pos:
            earliest_pos = pos
    
    # If no term is found, return the beginning of the text
    if earliest_pos == len(text):
        return highlight_terms(text[:snippet_length] + "...", query)
    
    # Calculate snippet start and end
    start = max(0, earliest_pos - snippet_length // 2)
    end = min(len(text), start + snippet_length)
    
    # Adjust start if end is at text length
    if end == len(text):
        start = max(0, end - snippet_length)
    
    snippet = text[start:end]
    
    # Add ellipsis if snippet is not at the start or end of the text
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."
    
    return highlight_terms(snippet, query)

def highlight_terms(text, query):
    highlighted = text
    for term in query.split():
        if len(term) < 2:
            continue

        # Create a regular expression pattern for case-insensitive matching
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        
        # Use the pattern to replace all occurrences with the highlighted version
        highlighted = pattern.sub(lambda m: f"<mark>{m.group()}</mark>", highlighted)
    
    return highlighted
