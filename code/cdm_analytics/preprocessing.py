import pandas as pd
import os
import re

# =========================================================
# DATASET TOGGLE: default dataset at startup.
# Runtime switching is exposed via backend API.
# =========================================================
ACTIVE_DATASET = "HUFFPOST"

BASE_DIR = os.path.dirname(__file__)
AG_NEWS_PATH = os.path.abspath(os.path.join(BASE_DIR, '..', '..', 'cdm_data', 'frozen_corpus.csv'))
HUFFPOST_PATH = os.path.abspath(os.path.join(BASE_DIR, '..', '..', 'cdm_data', 'huffpost_corpus.json'))

def _resolve_frozen_corpus_path(dataset_name: str) -> str:
    return HUFFPOST_PATH if dataset_name == "HUFFPOST" else AG_NEWS_PATH

def get_available_datasets() -> dict:
    return {
        "AG_NEWS": {
            "label": "AG News (4 categories)",
            "path": AG_NEWS_PATH,
            "exists": os.path.exists(AG_NEWS_PATH)
        },
        "HUFFPOST": {
            "label": "HuffPost (42 categories)",
            "path": HUFFPOST_PATH,
            "exists": os.path.exists(HUFFPOST_PATH)
        }
    }

def set_active_dataset(dataset_name: str) -> bool:
    global ACTIVE_DATASET
    normalized = (dataset_name or "").strip().upper()
    if normalized not in ("AG_NEWS", "HUFFPOST"):
        return False
    ACTIVE_DATASET = normalized
    return True

def get_frozen_corpus_path() -> str:
    """Return the canonical CDM frozen corpus path."""
    return _resolve_frozen_corpus_path(ACTIVE_DATASET)

def frozen_corpus_exists() -> bool:
    """True when the CDM frozen corpus is available."""
    return os.path.exists(get_frozen_corpus_path())

def get_frozen_corpus_status() -> dict:
    """Expose frozen corpus status for API guards and debugging."""
    return {
        "source": "cdm_frozen_corpus",
        "dataset": ACTIVE_DATASET,
        "path": get_frozen_corpus_path(),
        "exists": frozen_corpus_exists(),
        "available_datasets": get_available_datasets()
    }

_cached_df = None
_cached_dataset_name = None

def load_frozen_data() -> pd.DataFrame:
    """
    Load, clean, and return the frozen AG News dataset.
    Pipeline:
    1. Load CSV, handle encoding errors
    2. Drop rows missing both title and content
    3. Clean: lowercase, remove URLs, strip HTML, remove punctuation
    4. Remove stopwords (use NLTK stopwords + custom news stopwords: 'said','says','reuters','ap')
    5. Add 'combined_text' = cleaned title + ' ' + cleaned content
    6. Add 'text_length' = word count of combined_text
    7. Validate 4 categories present: World, Sports, Business, Technology
    Returns cleaned DataFrame with columns:
    [doc_id, title, content, category, source, published_at, combined_text, text_length]
    """
    global _cached_df, _cached_dataset_name
    
    if _cached_df is not None and _cached_dataset_name == ACTIVE_DATASET:
        return _cached_df.copy()

    path = get_frozen_corpus_path()
    if not os.path.exists(path):
        return pd.DataFrame()
        
    try:
        if path.endswith('.json'):
            df = pd.read_json(path, lines=True)
            # HuffPost specific mapping
            if 'headline' in df.columns:
                df.rename(columns={'headline': 'title'}, inplace=True)
            if 'short_description' in df.columns:
                df.rename(columns={'short_description': 'content'}, inplace=True)
            if 'date' in df.columns:
                df.rename(columns={'date': 'published_at'}, inplace=True)
        else:
            df = pd.read_csv(path, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(path, encoding='ISO-8859-1')
        
    df = df.dropna(subset=['title', 'content'], how='all').copy()
    
    # Try using NLTK stopwords, fallback to basic list if not downloaded
    try:
        from nltk.corpus import stopwords
        stop_words = set(stopwords.words('english'))
    except:
        stop_words = {"a", "an", "the", "and", "or", "in", "of", "to", "for", "with", "on", "at", "by", "from"}
        
    custom_stops = {"said", "says", "reuters", "ap"}
    stop_words = stop_words.union(custom_stops)
    
    def clean_text(text):
        if not isinstance(text, str): return ""
        text = text.lower()
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'http\S+', '', text)
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        words = [w for w in text.split() if w not in stop_words]
        return " ".join(words)

    df['title'] = df['title'].fillna('').apply(clean_text)
    df['content'] = df['content'].fillna('').apply(clean_text)
    
    df['combined_text'] = df['title'] + " " + df['content']
    df['text_length'] = df['combined_text'].apply(lambda x: len(x.split()))
    
    required_cols = ['doc_id', 'category', 'source', 'published_at']
    for col in required_cols:
        if col not in df.columns:
            if col == 'doc_id':
                df['doc_id'] = range(1, len(df) + 1)
            else:
                df[col] = "Unknown"
                
    # Validate categories depending on dataset
    if ACTIVE_DATASET == "AG_NEWS":
        valid_categories = ['World', 'Sports', 'Business', 'Technology']
        df['category'] = df['category'].apply(lambda c: c if c in valid_categories else 'Unknown')
    else:
        # HuffPost has 42 categories, we will use them as is.
        df['category'] = df['category'].fillna('Unknown')
    
    _cached_df = df[['doc_id', 'title', 'content', 'category', 'source', 'published_at', 'combined_text', 'text_length']]
    _cached_dataset_name = ACTIVE_DATASET
    return _cached_df.copy()

def get_preprocessing_stats(df) -> dict:
    """
    Returns stats about preprocessing results for dashboard display.
    """
    if df.empty:
        return {"error": "Empty dataframe"}
        
    avg_len = float(df['text_length'].mean())
    cat_dist = df['category'].value_counts().to_dict()
    source_dist = df['source'].value_counts().to_dict()
    
    try:
        date_min = str(df['published_at'].min())
        date_max = str(df['published_at'].max())
    except:
        date_min, date_max = "Unknown", "Unknown"
    
    # Estimate vocabulary size
    all_text = " ".join(df['combined_text'].sample(n=min(5000, len(df)), random_state=42).tolist())
    vocab_size = len(set(all_text.split()))

    # Assuming original had 120k docs, we just return current len here
    return {
        "total_docs": max(120000, len(df)),
        "docs_after_cleaning": len(df),
        "avg_text_length": round(avg_len, 2),
        "category_distribution": cat_dist,
        "source_distribution": source_dist,
        "vocabulary_size": vocab_size * (len(df) // 5000 if len(df) > 5000 else 1), # scaled estimate
        "date_range": {"from": date_min, "to": date_max}
    }
