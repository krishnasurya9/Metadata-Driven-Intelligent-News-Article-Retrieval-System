"""
Text Preprocessor Module
Handles text cleaning, tokenization, and normalization for IR
"""

import re
import string
from typing import List, Set

# Common English stopwords
STOPWORDS: Set[str] = {
    'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
    'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after',
    'above', 'below', 'between', 'under', 'again', 'further', 'then', 'once',
    'here', 'there', 'when', 'where', 'why', 'how', 'all', 'each', 'few', 'more',
    'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same',
    'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 'should',
    'now', 'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you',
    'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself',
    'she', 'her', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them',
    'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this',
    'that', 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been',
    'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing',
    'would', 'could', 'ought', 'im', 'youre', 'hes', 'shes', 'its', 'were',
    'theyre', 'ive', 'youve', 'weve', 'theyve', 'id', 'youd', 'hed', 'shed',
    'wed', 'theyd', 'ill', 'youll', 'hell', 'shell', 'well', 'theyll', 'isnt',
    'arent', 'wasnt', 'werent', 'hasnt', 'havent', 'hadnt', 'doesnt', 'dont',
    'didnt', 'wont', 'wouldnt', 'shant', 'shouldnt', 'cant', 'cannot', 'couldnt',
    'mustnt', 'lets', 'thats', 'whos', 'whats', 'heres', 'theres', 'whens',
    'wheres', 'whys', 'hows', 'also', 'said', 'says', 'say', 'according'
}


def clean_text(text: str) -> str:
    """
    Clean text by removing special characters and extra whitespace
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove URLs
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    
    # Remove email addresses
    text = re.sub(r'\S+@\S+', '', text)
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove special characters but keep spaces
    text = re.sub(r'[^\w\s]', ' ', text)
    
    # Remove numbers (optional - keep for news articles)
    # text = re.sub(r'\d+', '', text)
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    return text


def tokenize(text: str) -> List[str]:
    """
    Tokenize text into words
    """
    if not text:
        return []
    
    # Simple whitespace tokenization
    tokens = text.split()
    
    # Filter out very short tokens
    tokens = [t for t in tokens if len(t) > 1]
    
    return tokens


def remove_stopwords(tokens: List[str]) -> List[str]:
    """
    Remove stopwords from token list
    """
    return [t for t in tokens if t not in STOPWORDS]


import nltk
from nltk.stem import PorterStemmer

# Ensure NLTK data is available
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('punkt_tab', quiet=True)

# Initialize Stemmer
_stemmer = PorterStemmer()

def preprocess_text(text: str, remove_stops: bool = True, stem: bool = True) -> str:
    """
    Full preprocessing pipeline: clean, tokenize, remove stopwords, stem
    Returns space-separated tokens
    """
    cleaned = clean_text(text)
    tokens = tokenize(cleaned)
    
    if remove_stops:
        tokens = remove_stopwords(tokens)
        
    if stem:
        tokens = [_stemmer.stem(t) for t in tokens]
    
    return ' '.join(tokens)


def preprocess_for_tfidf(text: str) -> str:
    """
    Preprocess text specifically for TF-IDF vectorization
    """
    return preprocess_text(text, remove_stops=True)


def extract_keywords(text: str, top_n: int = 10) -> List[str]:
    """
    Extract top keywords from text based on word frequency
    Useful for generating tags if not available
    """
    from collections import Counter
    
    cleaned = clean_text(text)
    tokens = tokenize(cleaned)
    tokens = remove_stopwords(tokens)
    
    # Count word frequencies
    word_counts = Counter(tokens)
    
    # Get top N words
    top_words = [word for word, count in word_counts.most_common(top_n)]
    
    return top_words


def get_word_count(text: str) -> int:
    """
    Get word count of raw text
    """
    if not text or not isinstance(text, str):
        return 0
    return len(text.split())


def highlight_query_terms(text: str, query_terms: List[str], 
                          highlight_tag: str = "mark") -> str:
    """
    Highlight query terms in text for display
    """
    if not text or not query_terms:
        return text
    
    for term in query_terms:
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        text = pattern.sub(f'<{highlight_tag}>{term}</{highlight_tag}>', text)
    
    return text
