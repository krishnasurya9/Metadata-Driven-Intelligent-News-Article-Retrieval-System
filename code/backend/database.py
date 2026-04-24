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
    print(f"Attempting to connect to DuckDB at: {DB_PATH}")
    try:
        conn = duckdb.connect(DB_PATH)
        print("Successfully connected to DuckDB.")
        return conn
    except Exception as e:
        print(f"Error connecting to DuckDB: {e}")
        raise

def get_db_status() -> Dict[str, Any]:
    """Check database status"""
    try:
        conn = get_connection()
        count = conn.execute("SELECT COUNT(*) FROM news_articles").fetchone()[0]
        conn.close()
        return {
            "status": "online",
            "message": "Connected to DuckDB successfully.",
            "document_count": count
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

def init_database():
    """Initialize the database with the news_articles table"""
    print("Initializing database...")
    conn = get_connection()
    try:
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
        print("Table 'news_articles' checked/created.")
        
        # Migration: Add url column if it doesn't exist
        try:
            conn.execute("ALTER TABLE news_articles ADD COLUMN url TEXT")
            print("URL column checked/added.")
        except duckdb.CatalogException:
            print("URL column already exists.")
        except Exception as e:
            print(f"Error altering table for URL column: {e}")
            
        # Migration: Add image column if it doesn't exist
        try:
            conn.execute("ALTER TABLE news_articles ADD COLUMN image TEXT")
            print("Image column checked/added.")
        except duckdb.CatalogException:
            pass
        except Exception as e:
            print(f"Error altering table for image column: {e}")
            
    finally:
        conn.close()
        print("Database initialization complete.")
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
        image = art.get('image')
        
        conn.execute("""
            INSERT INTO news_articles 
            (doc_id, title, content, category, tags, source, published_at, word_count, url, image)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (next_id, title, content, category, 'live-news', source, published_at, word_count, url, image))
        
        next_id += 1
        new_count += 1
        
        # Update cache to prevent dupes within the same batch
        if url: existing_urls.add(url)
        if title: existing_titles.add(title)
        
    conn.close()
    return new_count


def load_articles_from_csv(file_path: str, mode: str = 'replace') -> Dict[str, Any]:
    """
    Smart Auto-Ingest: Load any CSV into the warehouse.
    Automatically detects and maps columns to the warehouse schema.
    
    mode: 'replace' = clear existing data first, 'append' = add to existing data
    """
    import pandas as pd
    
    if not os.path.exists(file_path):
        return {"status": "error", "message": f"File not found: {file_path}"}
    
    try:
        if file_path.endswith('.json'):
            df = pd.read_json(file_path, lines=True)
            # Pre-map HuffPost JSON columns to make auto-schema mapping easier
            if 'headline' in df.columns: df.rename(columns={'headline': 'title'}, inplace=True)
            if 'short_description' in df.columns: df.rename(columns={'short_description': 'content'}, inplace=True)
            if 'date' in df.columns: df.rename(columns={'date': 'published_at'}, inplace=True)
        else:
            # Read CSV with automatic encoding detection
            try:
                df = pd.read_csv(file_path, low_memory=False)
            except UnicodeDecodeError:
                df = pd.read_csv(file_path, encoding='latin-1', low_memory=False)
        
        original_cols = list(df.columns)
        original_rows = len(df)
        
        # ── Smart Schema Mapping ──────────────────────────────────────
        # Define known aliases for each warehouse field (case-insensitive)
        SCHEMA_ALIASES = {
            'title': [
                'title', 'headline', 'headline_text', 'heading', 'name',
                'summary', 'subject', 'article_title', 'news_title', 'head'
            ],
            'content': [
                'content', 'text', 'body', 'description', 'article_text',
                'article', 'full_text', 'news_text', 'story', 'abstract',
                'article_content', 'news_body', 'detail', 'details'
            ],
            'category': [
                'category', 'label', 'topic', 'headline_category', 'section',
                'class', 'type', 'genre', 'news_category', 'classification',
                'tag', 'department'
            ],
            'source': [
                'source', 'publication', 'publisher', 'author', 'outlet',
                'newspaper', 'provider', 'media', 'news_source', 'origin',
                'channel', 'website'
            ],
            'published_at': [
                'published_at', 'date', 'pubdate', 'publish_date',
                'published_date', 'publication_date', 'datetime', 'timestamp',
                'created_at', 'pub_date', 'news_date', 'article_date', 'time'
            ],
            'url': [
                'url', 'link', 'guid', 'href', 'web_url', 'article_url',
                'news_url', 'source_url', 'permalink'
            ],
            'doc_id': [
                'doc_id', 'id', 'article_id', 'news_id', 'index', 'sr_no'
            ]
        }
        
        # Build mapping: check each CSV column against aliases
        col_lower_map = {col.lower().strip(): col for col in df.columns}
        mapped = {}
        mapping_log = {}
        
        for target_field, aliases in SCHEMA_ALIASES.items():
            for alias in aliases:
                if alias.lower() in col_lower_map:
                    original_name = col_lower_map[alias.lower()]
                    mapped[target_field] = original_name
                    mapping_log[original_name] = target_field
                    break
        
        # Apply the mapping
        rename_map = {v: k for k, v in mapped.items()}
        df = df.rename(columns=rename_map)
        
        # ── Auto-derive missing fields ────────────────────────────────
        file_basename = os.path.splitext(os.path.basename(file_path))[0]
        
        # If no title but content exists, truncate content
        if 'title' not in df.columns:
            if 'content' in df.columns:
                df['title'] = df['content'].fillna('').str[:120] + '...'
            else:
                df['title'] = f'Article from {file_basename}'
        
        # If no content but title exists, use title as content
        if 'content' not in df.columns:
            if 'title' in df.columns:
                df['content'] = df['title']
            else:
                df['content'] = ''
        
        # Fill missing fields with sensible defaults
        if 'category' not in df.columns:
            df['category'] = 'general'
        if 'source' not in df.columns:
            # Derive source from filename (e.g., bbc_news.csv → BBC News)
            df['source'] = file_basename.replace('_', ' ').replace('-', ' ').title()
        if 'tags' not in df.columns:
            df['tags'] = ''
        if 'url' not in df.columns:
            df['url'] = ''
        
        # Parse dates intelligently
        if 'published_at' not in df.columns:
            df['published_at'] = None
        else:
            df['published_at'] = pd.to_datetime(df['published_at'], 
                                                  format='mixed', 
                                                  dayfirst=False, 
                                                  errors='coerce')
        
        # Compute word count
        if 'word_count' not in df.columns:
            df['word_count'] = df['content'].fillna('').str.split().str.len()
        
        # Auto-assign doc_ids (will be renumbered below)
        if 'doc_id' not in df.columns:
            df['doc_id'] = 0  # placeholder, assigned below
        
        # ── Clean the data ────────────────────────────────────────────
        # Drop rows with no title AND no content
        df = df.dropna(subset=['title', 'content'], how='all')
        
        # Fill NaN in text columns
        df['title'] = df['title'].fillna('')
        df['content'] = df['content'].fillna('')
        df['category'] = df['category'].fillna('general')
        df['source'] = df['source'].fillna(file_basename)
        df['tags'] = df['tags'].fillna('')
        df['url'] = df['url'].fillna('')
        if 'image' not in df.columns:
            df['image'] = None
        df['image'] = df['image'].fillna('')
        df['word_count'] = df['word_count'].fillna(0).astype(int)
        
        # Select only schema columns
        schema_cols = ['doc_id', 'title', 'content', 'category', 'tags', 
                       'source', 'published_at', 'word_count', 'url', 'image']
        for col in schema_cols:
            if col not in df.columns:
                df[col] = None
        df = df[schema_cols]
        
        # ── Insert into warehouse ─────────────────────────────────────
        conn = get_connection()
        
        if mode == 'replace':
            conn.execute("DELETE FROM news_articles")
            start_id = 1
        else:
            # Append: get next available doc_id
            max_id = conn.execute("SELECT COALESCE(MAX(doc_id), 0) FROM news_articles").fetchone()[0]
            start_id = max_id + 1
        
        # Assign sequential doc_ids
        df['doc_id'] = range(start_id, start_id + len(df))
        
        # Insert
        conn.execute("INSERT INTO news_articles SELECT * FROM df")
        
        total_count = conn.execute("SELECT COUNT(*) FROM news_articles").fetchone()[0]
        categories = conn.execute("SELECT DISTINCT category FROM news_articles").fetchall()
        sources_count = conn.execute("SELECT COUNT(DISTINCT source) FROM news_articles").fetchone()[0]
        
        conn.close()
        
        return {
            "status": "success",
            "documents_loaded": len(df),
            "total_in_warehouse": total_count,
            "categories_found": [c[0] for c in categories],
            "sources_found": sources_count,
            "schema_mapping": mapping_log,
            "original_columns": original_cols,
            "original_rows": original_rows,
            "mode": mode,
            "file": os.path.basename(file_path)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def execute_query(query: str, params: tuple = None) -> List[Dict]:
    """Execute a custom query and return results as a list of dicts"""
    conn = get_connection()
    if params:
        result = conn.execute(query, params)
    else:
        result = conn.execute(query)
        
    try:
        columns = [desc[0] for desc in result.description]
        rows = result.fetchall()
        conn.close()
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        conn.close()
        raise e


def get_all_articles() -> List[Dict]:
    """Get all articles from the database"""
    conn = get_connection()
    result = conn.execute("SELECT * FROM news_articles")
    columns = [desc[0] for desc in result.description]
    rows = result.fetchall()
    conn.close()
    return [dict(zip(columns, row)) for row in rows]


def get_article_by_id(doc_id: int) -> Optional[Dict]:
    """Get a single article by ID"""
    conn = get_connection()
    result = conn.execute("SELECT * FROM news_articles WHERE doc_id = ?", [doc_id]).fetchone()
    conn.close()
    if result:
        columns = [desc[0] for desc in result.description]
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
    
    result = conn.execute(query, params)
    columns = [desc[0] for desc in result.description]
    rows = result.fetchall()
    conn.close()
    return [dict(zip(columns, row)) for row in rows]


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
