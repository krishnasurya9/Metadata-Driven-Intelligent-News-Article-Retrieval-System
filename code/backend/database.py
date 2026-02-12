"""
Database Module - DuckDB Operations for News Articles
Handles all database connections and CRUD operations
"""

import duckdb
import os
from typing import List, Dict, Optional, Any

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'news_corpus.duckdb')


def get_connection():
    """Get a DuckDB connection"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return duckdb.connect(DB_PATH)


def init_database():
    """Initialize the database with the news_articles table"""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS news_articles (
            doc_id INTEGER PRIMARY KEY,
            title TEXT,
            content TEXT,
            category TEXT,
            tags TEXT,
            source TEXT,
            published_at DATE,
            word_count INTEGER,
            url TEXT
        )
    """)
    
    # Migration: Add url column if it doesn't exist
    try:
        conn.execute("ALTER TABLE news_articles ADD COLUMN url TEXT")
    except:
        pass  # Column likely exists
        
    conn.close()
    return {"status": "success", "message": "Database initialized"}


def save_articles(articles: List[Dict]) -> int:
    """
    Save new articles to the database (deduplicated by URL or Title)
    Returns the number of new articles added
    """
    if not articles:
        return 0
        
    conn = get_connection()
    
    # Get existing URLs/Titles to verify against
    existing = conn.execute("SELECT url, title FROM news_articles").fetchall()
    existing_urls = {row[0] for row in existing if row[0]}
    existing_titles = {row[1] for row in existing if row[1]}
    
    # Get next doc_id
    max_id = conn.execute("SELECT MAX(doc_id) FROM news_articles").fetchone()[0] or 0
    next_id = max_id + 1
    
    new_count = 0
    
    for art in articles:
        url = art.get('url')
        title = art.get('title')
        
        # Deduplication check
        if (url and url in existing_urls) or (title and title in existing_titles):
            continue
            
        # Prepare record
        content = art.get('description') or art.get('content') or title
        category = 'news' # Default for live news
        source = art.get('source') or 'Unknown'
        published_at = art.get('published_at')
        word_count = len(content.split()) if content else 0
        
        conn.execute("""
            INSERT INTO news_articles 
            (doc_id, title, content, category, tags, source, published_at, word_count, url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (next_id, title, content, category, 'live-news', source, published_at, word_count, url))
        
        next_id += 1
        new_count += 1
        
        # Update cache to prevent dupes within the same batch
        if url: existing_urls.add(url)
        if title: existing_titles.add(title)
        
    conn.close()
    return new_count


def load_articles_from_csv(file_path: str) -> Dict[str, Any]:
    """Load articles from a CSV file into the database"""
    import pandas as pd
    
    if not os.path.exists(file_path):
        return {"status": "error", "message": f"File not found: {file_path}"}
    
    try:
        df = pd.read_csv(file_path)
        
        # Map common column names to our schema
        column_mapping = {
            'id': 'doc_id',
            'headline': 'title',
            'Summary': 'title',  # Kaggle news-dataset
            'text': 'content',
            'Text': 'content',   # Kaggle news-dataset
            'body': 'content',
            'description': 'content',
            'date': 'published_at',
            'publication': 'source',
            'author': 'source',
            'label': 'category',
            'topic': 'category'
        }
        
        df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
        
        # Ensure required columns exist
        if 'doc_id' not in df.columns:
            df['doc_id'] = range(1, len(df) + 1)
        if 'title' not in df.columns and 'content' in df.columns:
            df['title'] = df['content'].str[:100] + '...'
        if 'tags' not in df.columns:
            df['tags'] = ''
        if 'word_count' not in df.columns and 'content' in df.columns:
            df['word_count'] = df['content'].fillna('').str.split().str.len()
        if 'category' not in df.columns:
            df['category'] = 'general'
        if 'source' not in df.columns:
            df['source'] = 'unknown'
        if 'published_at' not in df.columns:
            df['published_at'] = None
            
        # Select only our schema columns
        schema_cols = ['doc_id', 'title', 'content', 'category', 'tags', 'source', 'published_at', 'word_count']
        df = df[[c for c in schema_cols if c in df.columns]]
        
        # Insert into database
        conn = get_connection()
        conn.execute("DELETE FROM news_articles")  # Clear existing data
        conn.execute("INSERT INTO news_articles SELECT * FROM df")
        
        count = conn.execute("SELECT COUNT(*) FROM news_articles").fetchone()[0]
        categories = conn.execute("SELECT DISTINCT category FROM news_articles").fetchall()
        
        conn.close()
        
        return {
            "status": "success",
            "documents_loaded": count,
            "categories_found": [c[0] for c in categories],
            "columns_mapped": list(df.columns)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_all_articles() -> List[Dict]:
    """Get all articles from the database"""
    conn = get_connection()
    result = conn.execute("SELECT * FROM news_articles").fetchall()
    columns = ['doc_id', 'title', 'content', 'category', 'tags', 'source', 'published_at', 'word_count']
    conn.close()
    return [dict(zip(columns, row)) for row in result]


def get_article_by_id(doc_id: int) -> Optional[Dict]:
    """Get a single article by ID"""
    conn = get_connection()
    result = conn.execute("SELECT * FROM news_articles WHERE doc_id = ?", [doc_id]).fetchone()
    conn.close()
    if result:
        columns = ['doc_id', 'title', 'content', 'category', 'tags', 'source', 'published_at', 'word_count']
        return dict(zip(columns, result))
    return None


def get_articles_by_filter(category: str = None, source: str = None, 
                           date_from: str = None, date_to: str = None) -> List[Dict]:
    """Get articles with optional filters"""
    conn = get_connection()
    query = "SELECT * FROM news_articles WHERE 1=1"
    params = []
    
    if category:
        query += " AND category = ?"
        params.append(category)
    if source:
        query += " AND source = ?"
        params.append(source)
    if date_from:
        query += " AND published_at >= ?"
        params.append(date_from)
    if date_to:
        query += " AND published_at <= ?"
        params.append(date_to)
    
    result = conn.execute(query, params).fetchall()
    columns = ['doc_id', 'title', 'content', 'category', 'tags', 'source', 'published_at', 'word_count']
    conn.close()
    return [dict(zip(columns, row)) for row in result]


def get_category_distribution() -> Dict[str, int]:
    """Get count of articles per category"""
    conn = get_connection()
    result = conn.execute("""
        SELECT category, COUNT(*) as count 
        FROM news_articles 
        GROUP BY category 
        ORDER BY count DESC
    """).fetchall()
    conn.close()
    return {row[0]: row[1] for row in result}


def get_source_distribution() -> Dict[str, int]:
    """Get count of articles per source"""
    conn = get_connection()
    result = conn.execute("""
        SELECT source, COUNT(*) as count 
        FROM news_articles 
        GROUP BY source 
        ORDER BY count DESC
        LIMIT 20
    """).fetchall()
    conn.close()
    return {row[0]: row[1] for row in result}


def get_time_distribution() -> List[Dict]:
    """Get count of articles over time"""
    conn = get_connection()
    result = conn.execute("""
        SELECT 
            strftime('%Y-%m', published_at) as month,
            COUNT(*) as count 
        FROM news_articles 
        WHERE published_at IS NOT NULL
        GROUP BY month 
        ORDER BY month
    """).fetchall()
    conn.close()
    return [{"month": row[0], "count": row[1]} for row in result]


def get_corpus_stats() -> Dict[str, Any]:
    """Get overall corpus statistics"""
    conn = get_connection()
    stats = {}
    
    stats['total_documents'] = conn.execute("SELECT COUNT(*) FROM news_articles").fetchone()[0]
    stats['total_categories'] = conn.execute("SELECT COUNT(DISTINCT category) FROM news_articles").fetchone()[0]
    stats['total_sources'] = conn.execute("SELECT COUNT(DISTINCT source) FROM news_articles").fetchone()[0]
    stats['avg_word_count'] = conn.execute("SELECT AVG(word_count) FROM news_articles").fetchone()[0] or 0
    
    date_range = conn.execute("""
        SELECT MIN(published_at), MAX(published_at) 
        FROM news_articles 
        WHERE published_at IS NOT NULL
    """).fetchone()
    stats['date_range'] = {"from": str(date_range[0]), "to": str(date_range[1])} if date_range[0] else None
    
    conn.close()
    return stats


# Initialize database on module import
init_database()
