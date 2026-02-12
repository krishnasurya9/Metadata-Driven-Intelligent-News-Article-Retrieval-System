"""
Mediastack API Service - Fetch live news from mediastack.com
Provides high-volume news retrieval with multiple API key support
"""

import requests
import os
from typing import List, Dict, Any, Optional

MEDIASTACK_API_URL = "http://api.mediastack.com/v1/news"


def fetch_mediastack_news(
    api_key: str,
    keywords: Optional[str] = None,
    categories: Optional[str] = None,
    countries: Optional[str] = None,
    languages: str = "en",
    sort: str = "published_desc",
    limit: int = 100,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    Fetch live news from Mediastack API
    
    Args:
        api_key: Mediastack API key
        keywords: Search keywords (optional)
        categories: Comma-separated categories to include/exclude (optional)
                   Example: "technology,business,-sports"
        countries: Comma-separated country codes (optional)
        languages: Language codes (default: "en")
        sort: Sorting order - "published_desc" (default), "published_asc", "popularity"
        limit: Number of results (1-100, default: 100)
        offset: Pagination offset (default: 0)
        
    Returns:
        List of standardized article dictionaries
    """
    if not api_key:
        print("Mediastack: No API key provided")
        return []
    
    params = {
        'access_key': api_key,
        'languages': languages,
        'sort': sort,
        'limit': min(limit, 100),  # API max is 100
        'offset': offset
    }
    
    # Add optional filters
    if keywords:
        params['keywords'] = keywords
    
    if categories:
        params['categories'] = categories
    
    if countries:
        params['countries'] = countries
    
    try:
        response = requests.get(MEDIASTACK_API_URL, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check for API errors
            if 'error' in data:
                error_info = data['error']
                print(f"Mediastack API Error: {error_info.get('code')} - {error_info.get('message')}")
                return []
            
            raw_articles = data.get('data', [])
            
            # Standardize to our app's format
            articles = []
            for item in raw_articles:
                # Skip articles without title or URL
                if not item.get('title') or not item.get('url'):
                    continue
                
                article = {
                    "title": item.get('title'),
                    "url": item.get('url'),
                    "image": item.get('image'),
                    "source": item.get('source', 'Unknown'),
                    "published_at": item.get('published_at'),
                    "description": item.get('description'),
                    "content": item.get('description'),  # Mediastack doesn't provide full content
                    "category": item.get('category', 'general').lower() if item.get('category') else 'general',
                    "country": item.get('country'),
                    "language": item.get('language', 'en')
                }
                articles.append(article)
            
            print(f"Mediastack: Retrieved {len(articles)} articles")
            return articles
            
        else:
            print(f"Mediastack HTTP Error: {response.status_code} - {response.text[:200]}")
            return []
            
    except requests.exceptions.Timeout:
        print("Mediastack: Request timeout")
        return []
    except Exception as e:
        print(f"Mediastack Exception: {e}")
        return []


def fetch_with_multiple_keys(
    api_keys: List[str],
    categories: Optional[str] = None,
    limit_per_key: int = 100
) -> List[Dict[str, Any]]:
    """
    Fetch news using multiple API keys to get more results
    
    Args:
        api_keys: List of Mediastack API keys
        categories: Categories to fetch (optional)
        limit_per_key: Results per key (default: 100)
        
    Returns:
        Combined list of articles from all keys
    """
    all_articles = []
    seen_urls = set()
    
    for i, key in enumerate(api_keys):
        print(f"Fetching with Mediastack key {i+1}/{len(api_keys)}...")
        
        # Fetch articles
        articles = fetch_mediastack_news(
            api_key=key,
            categories=categories,
            limit=limit_per_key,
            sort="published_desc"
        )
        
        # Deduplicate by URL
        for article in articles:
            url = article.get('url')
            if url and url not in seen_urls:
                seen_urls.add(url)
                all_articles.append(article)
    
    print(f"Mediastack: Total unique articles from {len(api_keys)} keys: {len(all_articles)}")
    return all_articles


if __name__ == "__main__":
    # Test the service
    from dotenv import load_dotenv
    load_dotenv()
    
    key = os.getenv('MEDIASTACK_API_KEY_1')
    if key:
        print("Testing Mediastack API...")
        articles = fetch_mediastack_news(
            api_key=key,
            categories="technology,business",
            limit=10
        )
        
        print(f"\nFetched {len(articles)} articles")
        if articles:
            print("\nFirst article:")
            print(f"  Title: {articles[0]['title']}")
            print(f"  Source: {articles[0]['source']}")
            print(f"  Category: {articles[0]['category']}")
            print(f"  Published: {articles[0]['published_at']}")
    else:
        print("No MEDIASTACK_API_KEY_1 found in .env file")
