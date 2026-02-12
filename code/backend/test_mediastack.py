"""Test script for mediastack service"""
from mediastack_service import fetch_mediastack_news
import os
from dotenv import load_dotenv

load_dotenv()

key = os.getenv('MEDIASTACK_API_KEY_1')
print('Testing Mediastack API...')
print(f'API Key: {key[:10]}...' if key else 'No key found')

if key:
    articles = fetch_mediastack_news(key, categories='technology', limit=10)
    print(f'\nFetched {len(articles)} articles')
    
    if articles:
        print(f'\nFirst article:')
        print(f'  Title: {articles[0]["title"]}')
        print(f'  Source: {articles[0]["source"]}')
        print(f'  Category: {articles[0]["category"]}')
        print(f'  Published: {articles[0]["published_at"]}')
    else:
        print('No articles fetched')
else:
    print('No MEDIASTACK_API_KEY_1 found in .env file')
