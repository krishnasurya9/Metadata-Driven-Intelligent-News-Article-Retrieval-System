"""
Background News Fetcher - Automatically fetch and cache news on startup
Runs in a separate thread to avoid blocking the Flask server
"""

import os
import threading
import time
from typing import List, Dict, Any
from dotenv import load_dotenv

# Import services
import guardian_service
import mediastack_service
import database
import ir_engine

# Load environment variables
load_dotenv()

# Global status tracking
_fetch_status = {
    "running": False,
    "completed": False,
    "total_fetched": 0,
    "total_archived": 0,
    "sources": {},
    "start_time": None,
    "end_time": None,
    "error": None
}


def get_status() -> Dict[str, Any]:
    """Get current background fetch status"""
    return _fetch_status.copy()


def _fetch_from_guardian() -> List[Dict[str, Any]]:
    """Fetch news from Guardian API"""
    all_articles = []
    
    guardian_key = os.getenv('GUARDIAN_API_KEY')
    if guardian_key:
        print("[*] Fetching from Guardian API...")
        
        # Fetch general news without specific query
        articles = guardian_service.fetch_guardian_news(guardian_key, query=None)
        
        if articles:
            all_articles.extend(articles)
            print(f"[+] Guardian: {len(articles)} articles")
            _fetch_status["sources"]["Guardian"] = len(articles)
    else:
        print("[!] No Guardian API key configured")
    
    return all_articles


def _fetch_from_mediastack() -> List[Dict[str, Any]]:
    """Fetch news from Mediastack API with multiple keys"""
    all_articles = []
    
    # Collect all mediastack API keys
    mediastack_keys = []
    i = 1
    while True:
        key = os.getenv(f'MEDIASTACK_API_KEY_{i}')
        if not key:
            break
        mediastack_keys.append(key)
        i += 1
    
    # Also check for single key
    single_key = os.getenv('MEDIASTACK_API_KEY')
    if single_key and single_key not in mediastack_keys:
        mediastack_keys.append(single_key)
    
    if mediastack_keys:
        print(f"[*] Fetching from Mediastack API ({len(mediastack_keys)} key(s))...")
        
        # Fetch diverse categories to get varied content
        categories_to_fetch = [
            "general,business,technology",  # Mix of general interest
            "science,health,sports",         # Other categories
            "entertainment"                   # Entertainment
        ]
        
        seen_urls = set()
        
        for category_group in categories_to_fetch:
            # Use multiple keys for each category group
            articles = mediastack_service.fetch_with_multiple_keys(
                api_keys=mediastack_keys,
                categories=category_group,
                limit_per_key=100  # Max per key
            )
            
            # Deduplicate
            for article in articles:
                url = article.get('url')
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    all_articles.append(article)
        
        print(f"[+] Mediastack: {len(all_articles)} unique articles")
        _fetch_status["sources"]["Mediastack"] = len(all_articles)
    else:
        print("[!] No Mediastack API keys configured")
    
    return all_articles


def _fetch_from_newsapi() -> List[Dict[str, Any]]:
    """Fetch news from NewsAPI (existing implementation)"""
    import requests
    
    all_articles = []
    
    # Collect NewsAPI keys
    news_api_keys = []
    i = 1
    while True:
        key = os.getenv(f'NEWS_API_KEY_{i}')
        if not key:
            break
        news_api_keys.append(key)
        i += 1
    
    if os.getenv('NEWS_API_KEY'):
        news_api_keys.append(os.getenv('NEWS_API_KEY'))
    
    if news_api_keys:
        print(f"[*] Fetching from NewsAPI ({len(news_api_keys)} key(s))...")
        
        seen_urls = set()
        
        for i, key in enumerate(news_api_keys):
            try:
                url = "https://newsapi.org/v2/top-headlines"
                params = {
                    'country': 'us',
                    'apiKey': key,
                    'pageSize': 100  # Max allowed
                }
                
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    for art in data.get('articles', []):
                        article_url = art.get('url')
                        if article_url and article_url not in seen_urls:
                            seen_urls.add(article_url)
                            
                            all_articles.append({
                                "title": art.get('title'),
                                "url": article_url,
                                "image": art.get('urlToImage'),
                                "source": art.get('source', {}).get('name'),
                                "published_at": art.get('publishedAt'),
                                "description": art.get('description'),
                                "content": art.get('content'),
                                "category": "general"
                            })
            except Exception as e:
                print(f"[!] NewsAPI key {i+1} error: {e}")
        
        print(f"[+] NewsAPI: {len(all_articles)} unique articles")
        _fetch_status["sources"]["NewsAPI"] = len(all_articles)
    else:
        print("[!] No NewsAPI keys configured")
    
    return all_articles


def _background_fetch_task():
    """Main background fetch task - runs in separate thread"""
    global _fetch_status
    
    try:
        _fetch_status["running"] = True
        _fetch_status["start_time"] = time.time()
        
        print("\n" + "="*60)
        print("[*] Starting Background News Fetch")
        print("="*60)
        
        all_articles = []
        
        # Fetch from all sources
        all_articles.extend(_fetch_from_guardian())
        all_articles.extend(_fetch_from_mediastack())
        all_articles.extend(_fetch_from_newsapi())
        
        _fetch_status["total_fetched"] = len(all_articles)
        
        if all_articles:
            print(f"\n[*] Total articles fetched: {len(all_articles)}")
            print("[*] Saving to database...")
            
            # Save to database (deduplication happens here)
            saved_count = database.save_articles(all_articles)
            _fetch_status["total_archived"] = saved_count
            
            print(f"[+] Archived {saved_count} new articles")
            
            # Rebuild search index
            print("[*] Rebuilding search index...")
            all_docs = database.get_all_articles()
            ir_engine.build_index(all_docs)
            
            print("[+] Search index updated")
        else:
            print("[!] No articles fetched from any source")
        
        _fetch_status["completed"] = True
        _fetch_status["end_time"] = time.time()
        
        duration = _fetch_status["end_time"] - _fetch_status["start_time"]
        print(f"\n[+] Background fetch completed in {duration:.2f}s")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n[!] Background fetch error: {e}")
        _fetch_status["error"] = str(e)
    finally:
        _fetch_status["running"] = False


def start_background_fetch():
    """
    Start background news fetching in a separate thread
    Non-blocking - returns immediately
    """
    global _fetch_status
    
    # Reset status
    _fetch_status = {
        "running": False,
        "completed": False,
        "total_fetched": 0,
        "total_archived": 0,
        "sources": {},
        "start_time": None,
        "end_time": None,
        "error": None
    }
    
    # Start thread
    thread = threading.Thread(target=_background_fetch_task, daemon=True)
    thread.start()
    
    print("[*] Background news fetch started in separate thread...")


if __name__ == "__main__":
    # Test the fetcher
    print("Testing background news fetcher...")
    start_background_fetch()
    
    # Wait for completion
    while _fetch_status["running"] or not _fetch_status["completed"]:
        time.sleep(1)
    
    print("\nFinal status:")
    print(_fetch_status)
