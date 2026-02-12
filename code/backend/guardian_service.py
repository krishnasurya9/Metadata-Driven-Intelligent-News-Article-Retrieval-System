import requests
import os
from typing import List, Dict, Any

GUARDIAN_API_URL = "https://content.guardianapis.com/search"

def fetch_guardian_news(api_key: str, query: str = None) -> List[Dict[str, Any]]:
    """
    Fetch live news from The Guardian API
    
    Args:
        api_key: The Guardian API key
        query: Optional search query (default: None for general top news)
        
    Returns:
        List of standardized article dictionaries
    """
    if not api_key:
        return []
        
    params = {
        'api-key': api_key,
        'show-fields': 'bodyText,thumbnail,byline,headline',
        'page-size': 20,
        'order-by': 'newest'
    }
    
    # If no query, we can target generic sections for "top news" feel
    if query:
        params['q'] = query
    else:
        # Default mix of sections for a "homepage" feel if no query provided
        params['section'] = 'world|technology|business|science|environment'
        
    try:
        response = requests.get(GUARDIAN_API_URL, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('response', {}).get('results', [])
            
            articles = []
            for item in results:
                fields = item.get('fields', {})
                
                # Standardize to our app's format
                article = {
                    "title": item.get('webTitle'),
                    "url": item.get('webUrl'),
                    "image": fields.get('thumbnail'),
                    "source": "The Guardian", # Explicit source
                    "published_at": item.get('webPublicationDate'),
                    "description": fields.get('headline'), # Use headline as description/summary
                    "content": fields.get('bodyText'), # FULL TEXT!
                    "category": item.get('sectionName', 'News').lower()
                }
                articles.append(article)
                
            return articles
            
        else:
            print(f"Guardian API Error: {response.status_code} - {response.text}")
            return []
            
    except Exception as e:
        print(f"Guardian Fetch Exception: {e}")
        return []
