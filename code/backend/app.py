"""
News Article Retrieval & Analytics System - Flask Backend
Main application with all API endpoints
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os

import database
import ir_engine
import analytics_engine
import mining_engine
import llm_service

import news_fetcher
from dotenv import load_dotenv

import guardian_service

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable cross-origin requests for frontend

# Store last search results for analytics comparison
_last_search_results = {"top": [], "bottom": []}


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    index_info = ir_engine.get_index_info()
    llm_status = llm_service.get_status()
    
    return jsonify({
        "status": "healthy",
        "database": "connected",
        "index": index_info.get('status', 'not_built'),
        "llm": llm_status.get('status', 'unavailable'),
        "documents_indexed": index_info.get('documents_indexed', 0)
    })


@app.route('/api/data/load', methods=['POST'])
def load_data():
    """Load dataset from CSV file"""
    data = request.get_json() or {}
    file_path = data.get('file_path')
    
    if not file_path:
        # Default path
        file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'news_articles.csv')
    
    # Make path absolute if relative
    if not os.path.isabs(file_path):
        file_path = os.path.join(os.path.dirname(__file__), '..', file_path)
    
    mode = data.get('mode', 'replace')  # 'replace' or 'append'
    
    # Load into database with smart schema mapping
    result = database.load_articles_from_csv(file_path, mode=mode)
    
    if result.get('status') == 'success':
        # Build search index
        documents = database.get_all_articles()
        index_result = ir_engine.build_index(documents)
        result['index'] = index_result
    
    return jsonify(result)


@app.route('/api/data/upload', methods=['POST'])
def upload_csv():
    """Upload a CSV file and ingest into the warehouse"""
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '' or not file.filename.endswith('.csv'):
        return jsonify({"status": "error", "message": "Please upload a valid CSV file"}), 400
    
    # Save to data directory
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    os.makedirs(data_dir, exist_ok=True)
    save_path = os.path.join(data_dir, file.filename)
    file.save(save_path)
    
    # Ingest into warehouse (uploads always append by default)
    mode = request.form.get('mode', 'append')
    result = database.load_articles_from_csv(save_path, mode=mode)
    
    if result.get('status') == 'success':
        documents = database.get_all_articles()
        index_result = ir_engine.build_index(documents)
        result['index'] = index_result
        result['file_saved'] = file.filename
    
    return jsonify(result)


@app.route('/api/data/info', methods=['GET'])
def data_info():
    """Return info about locally available data files"""
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    files = []
    if os.path.exists(data_dir):
        for f in os.listdir(data_dir):
            fp = os.path.join(data_dir, f)
            if os.path.isfile(fp):
                size_mb = round(os.path.getsize(fp) / (1024 * 1024), 2)
                files.append({"name": f, "size_mb": size_mb, "path": fp})
    
    # Current warehouse stats
    stats = database.get_corpus_stats()
    
    return jsonify({
        "local_files": files,
        "warehouse": stats,
        "default_csv": "news_articles.csv"
    })


@app.route('/api/search', methods=['POST'])
def search():
    """
    IR Search endpoint
    Returns top and bottom ranked results with explanations
    """
    global _last_search_results
    
    data = request.get_json() or {}
    query = data.get('query', '')
    
    if not query:
        return jsonify({"status": "error", "message": "Query is required"}), 400
    
    # Get filters
    filters = data.get('filters', {})
    boost_recency = data.get('boost_recency', False)
    boost_category = data.get('boost_category', False)
    target_category = filters.get('category')
    top_k = data.get('top_k', 20)
    
    # Get all documents
    documents = database.get_all_articles()
    
    if not documents:
        # Try to load default data if DB is empty
        initialize_system()
        documents = database.get_all_articles()
        if not documents:
             return jsonify({"status": "error", "message": "No documents in database. Please load data first."}), 400

    # --- Live Search (Hybrid) ---
    # Fetch fresh articles matching the query from Guardian API
    guardian_key = os.getenv('GUARDIAN_API_KEY')
    if guardian_key and query and len(query) > 3:
        print(f"Hybrid Search: Fetching live results for '{query}'...")
        try:
            # We don't want to block the search too long, so maybe limit this or make it fast
            live_articles = guardian_service.fetch_guardian_news(guardian_key, query)
            if live_articles:
                saved_count = database.save_articles(live_articles)
                if saved_count > 0:
                    print(f"Hybrid Search: Archived {saved_count} new articles.")
                    # Rebuild index to include new docs
                    # optimize: in production use incremental indexing
                    documents = database.get_all_articles() # Refresh list
                    ir_engine.build_index(documents) 
        except Exception as e:
            print(f"Hybrid Search Error: {e}")
            # Continue with local search even if live fetch fails

    # Perform search
    results = ir_engine.search(
        query=query,
        documents=documents,
        filters=filters,
        boost_recency=boost_recency,
        boost_category=boost_category,
        target_category=target_category,
        top_k=top_k
    )
    
    if results.get('status') != 'success':
        return jsonify(results), 400
        
    # Check for zero results and use LLM fallback
    if results.get('total_results', 0) == 0:
        general_answer = llm_service.generate_general_answer(query)
        
        # Create a "pseudo-result" or just return the summary
        # We'll return a success status with a specific flag
        return jsonify({
            "status": "success",
            "query": query,
            "total_results": 0,
            "top_results": [],
            "bottom_results": [],
            "llm_summary": general_answer,
            "fallback_mode": True
        })
    
    # Store for analytics
    _last_search_results = {
        "top": results.get('top_results', []),
        "bottom": results.get('bottom_results', [])
    }
    
    # Calculate metrics
    all_results = results.get('top_results', []) + results.get('bottom_results', [])
    metrics = ir_engine.calculate_metrics(all_results, k=top_k)
    results['metrics'] = metrics
    
    # Generate LLM summary
    llm_summary = llm_service.generate_search_summary(
        query=query,
        top_results=results.get('top_results', []),
        bottom_results=results.get('bottom_results', [])
    )
    results['llm_summary'] = llm_summary
    
    return jsonify(results)


@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """Get IR metrics for last search"""
    global _last_search_results
    
    corpus_stats = database.get_corpus_stats()
    index_info = ir_engine.get_index_info()
    
    # Calculate metrics on last results
    all_results = _last_search_results.get('top', []) + _last_search_results.get('bottom', [])
    last_query_stats = ir_engine.calculate_metrics(all_results) if all_results else None
    
    return jsonify({
        "total_documents": corpus_stats.get('total_documents', 0),
        "indexed_documents": index_info.get('documents_indexed', 0),
        "last_query_stats": last_query_stats,
        "formulas": {
            "precision": "Retrieved Relevant / Retrieved Total",
            "recall": "Retrieved Relevant / Total Relevant",
            "f1": "2 * (Precision * Recall) / (Precision + Recall)"
        }
    })


@app.route('/api/analytics', methods=['POST'])
def analytics():
    """
    Analytics/Mining endpoint
    Provides corpus-level and result-level analysis
    """
    global _last_search_results
    
    data = request.get_json() or {}
    mode = data.get('mode', 'corpus')  # 'corpus' or 'last_ir_results'
    analysis_type = data.get('analysis_type', 'category_distribution')
    
    # Get documents
    documents = database.get_all_articles()
    
    if not documents:
        return jsonify({"status": "error", "message": "No documents in database"}), 400
    
    # Determine which doc_ids to analyze
    doc_ids = None
    if mode == 'last_ir_results' and _last_search_results.get('top'):
        doc_ids = [r['doc_id'] for r in _last_search_results['top'] + _last_search_results['bottom']]
    
    # Perform analysis
    if analysis_type == 'category_distribution':
        result = analytics_engine.analyze_category_distribution(documents, doc_ids)
    
    elif analysis_type == 'term_frequency':
        result = analytics_engine.analyze_term_frequency(documents, doc_ids)
    
    elif analysis_type == 'source_bias':
        result = analytics_engine.analyze_source_bias(documents, doc_ids)
    
    elif analysis_type == 'time_trends':
        result = analytics_engine.analyze_time_trends(documents, doc_ids)
    
    elif analysis_type == 'top_bottom_comparison':
        if not _last_search_results.get('top'):
            return jsonify({"status": "error", "message": "No search results to compare. Run a search first."}), 400
        result = analytics_engine.compare_top_bottom(
            _last_search_results['top'],
            _last_search_results['bottom'],
            documents
        )
    
    elif analysis_type == 'corpus_overview':
        result = analytics_engine.get_corpus_overview(documents)
        result['analysis_type'] = 'corpus_overview'
    
    else:
        return jsonify({"status": "error", "message": f"Unknown analysis type: {analysis_type}"}), 400
    
    result['mode'] = mode
    result['mode'] = mode
    return jsonify(result)


@app.route('/api/mining/association', methods=['GET'])
def mining_association():
    """Generate association rules for tags"""
    try:
        min_support = float(request.args.get('min_support', 0.05))
        min_confidence = float(request.args.get('min_confidence', 0.2))
        
        result = mining_engine.generate_association_rules(min_support, min_confidence)
        if "error" in result:
             return jsonify({"status": "error", "message": result["error"]}), 400
             
        return jsonify({"status": "success", "data": result})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/mining/clustering', methods=['POST'])
def mining_clustering():
    """Perform K-Means clustering"""
    data = request.get_json() or {}
    n_clusters = int(data.get('n_clusters', 5))
    
    try:
        result = mining_engine.perform_clustering(n_clusters)
        if "error" in result:
             return jsonify({"status": "error", "message": result["error"]}), 400
             
        return jsonify({"status": "success", "data": result})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/mining/classification', methods=['POST'])
def mining_classification():
    """Train and evaluate category classifier"""
    try:
        result = mining_engine.train_classifier()
        if "error" in result:
             return jsonify({"status": "error", "message": result["error"]}), 400
             
        return jsonify({"status": "success", "data": result})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500



@app.route('/api/debug', methods=['GET'])
def debug_pipeline():
    """
    Pipeline explanation endpoint
    Shows all models and steps used
    """
    index_info = ir_engine.get_index_info()
    llm_status = llm_service.get_status()
    
    return jsonify({
        "pipeline_steps": [
            {"step": 1, "name": "Text Preprocessing", "description": "Lowercase, tokenize, remove stopwords (custom stopword list)"},
            {"step": 2, "name": "TF-IDF Vectorization", "description": "Convert text to TF-IDF vectors with max 10000 features, unigrams & bigrams"},
            {"step": 3, "name": "Cosine Similarity", "description": "Compute cosine similarity between query and document vectors"},
            {"step": 4, "name": "Metadata Boosting", "description": "Apply optional recency/category/tag boosts to base scores"},
            {"step": 5, "name": "Rank Stratification", "description": "Separate top 20 (high relevance) and bottom 20 (low relevance)"},
            {"step": 6, "name": "Explanation Generation", "description": "Generate explanations using LLM or rule-based fallback"}
        ],
        "models_used": [
            {"name": "TF-IDF", "purpose": "Relevance scoring - term frequency weighted by inverse document frequency"},
            {"name": "Cosine Similarity", "purpose": "Ranking - angle-based similarity in vector space"},
            {"name": "Metadata Boosting", "purpose": "Context awareness - recency, category, and tag alignment"},
            {"name": "Local LLM (Ollama)", "purpose": "Explanation generation only - never searches or ranks"}
        ],
        "current_config": {
            "vectorizer": "TF-IDF (sklearn)",
            "max_features": 10000,
            "ngram_range": "1-2",
            "similarity": "cosine",
            "boost_weights": {"recency": 0.05, "category": 0.15, "tags": 0.05}
        },
        "index_status": index_info,
        "llm_status": llm_status
    })


@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Get list of categories in the corpus"""
    distribution = database.get_category_distribution()
    return jsonify({
        "categories": list(distribution.keys()),
        "distribution": distribution
    })


@app.route('/api/sources', methods=['GET'])
def get_sources():
    """Get list of sources in the corpus"""
    distribution = database.get_source_distribution()
    return jsonify({
        "sources": list(distribution.keys()),
        "distribution": distribution
    })


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get corpus statistics"""
    stats = database.get_corpus_stats()
    return jsonify(stats)


@app.route('/api/llm/configure', methods=['POST'])
def configure_llm():
    """Configure LLM endpoint (for LM Studio)"""
    data = request.get_json() or {}
    host = data.get('host', 'localhost')
    port = data.get('port', 1234)
    
    result = llm_service.configure_lm_studio(host, port)
    return jsonify(result)


@app.route('/api/llm/status', methods=['GET'])
def llm_status():
    """Get LLM service status"""
    return jsonify(llm_service.get_status())


@app.route('/api/fetch-status', methods=['GET'])
def fetch_status():
    """Get background fetch status"""
    return jsonify(news_fetcher.get_status())


@app.route('/api/live-news', methods=['GET'])
def get_live_news():
    """
    Get live headlines from external API
    Supports multiple API keys via environment variables
    """
    import requests
    import random
    import guardian_service
    import mediastack_service
    
    articles = []
    
    # --- Source 1: The Guardian (High Quality, Full Text) ---
    guardian_key = os.getenv('GUARDIAN_API_KEY')
    if guardian_key:
        print("Fetching from The Guardian...")
        guardian_articles = guardian_service.fetch_guardian_news(guardian_key)
        if guardian_articles:
            articles.extend(guardian_articles)
            print(f"Retrieved {len(guardian_articles)} articles from The Guardian.")
    
    # --- Source 2: Mediastack (High Volume) ---
    mediastack_keys = []
    i = 1
    while True:
        key = os.getenv(f'MEDIASTACK_API_KEY_{i}')
        if not key:
            break
        mediastack_keys.append(key)
        i += 1
    
    if os.getenv('MEDIASTACK_API_KEY'):
        mediastack_keys.append(os.getenv('MEDIASTACK_API_KEY'))
    
    if mediastack_keys:
        print(f"Fetching from Mediastack ({len(mediastack_keys)} keys)...")
        mediastack_articles = mediastack_service.fetch_with_multiple_keys(
            api_keys=mediastack_keys,
            categories="general,technology,business",
            limit_per_key=100
        )
        if mediastack_articles:
            articles.extend(mediastack_articles)
            print(f"Retrieved {len(mediastack_articles)} articles from Mediastack.")
    
    # --- Source 3: NewsAPI (Aggregator) ---
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
        try:
            selected_key = random.choice(news_api_keys)
            url = "https://newsapi.org/v2/top-headlines"
            params = {
                'country': 'us',
                'apiKey': selected_key,
                'pageSize': 12
            }
            
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                newsapi_articles = []
                for art in data.get('articles', []):
                    newsapi_articles.append({
                        "title": art.get('title'),
                        "url": art.get('url'),
                        "image": art.get('urlToImage'),
                        "source": art.get('source', {}).get('name'),
                        "published_at": art.get('publishedAt'),
                        "description": art.get('description'),
                        "content": art.get('content') 
                    })
                articles.extend(newsapi_articles)
                print(f"Retrieved {len(newsapi_articles)} articles from NewsAPI.")
            else:
                print(f"NewsAPI Error: {response.status_code}")
                
        except Exception as e:
            print(f"NewsAPI Exception: {str(e)}")

    if not articles:
        return jsonify({
            "status": "error", 
            "message": "No articles retrieved. Check API keys for Guardian or NewsAPI."
        }), 503

    # AUTO-ARCHIVE: Save to local database
    # Deduplication happens inside save_articles logic
    saved_count = database.save_articles(articles)
    
    # If new articles were saved, update the index so they are searchable
    if saved_count > 0:
        print(f"Archived {saved_count} new articles from live feed.")
        all_docs = database.get_all_articles()
        ir_engine.build_index(all_docs)
    
    return jsonify({
        "status": "success", 
        "articles": articles,
        "archived_count": saved_count
    })


def initialize_system():
    """Check and initialize system with data if empty"""
    print("Checking system state...")
    stats = database.get_corpus_stats()
    
    # Start background news fetch regardless of database state
    print("\n[*] Initiating background news fetch...")
    news_fetcher.start_background_fetch()
    
    if stats.get('total_documents', 0) == 0:
        print("Database is empty. Attempting to load default dataset...")
        csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'news_articles.csv')
        
        if os.path.exists(csv_path):
            print(f"Found dataset at: {csv_path}")
            print("Loading data... This may take a moment.")
            
            result = database.load_articles_from_csv(csv_path)
            
            if result.get('status') == 'success':
                print(f"Successfully loaded {result.get('documents_loaded')} articles.")
                
                print("Building search index...")
                documents = database.get_all_articles()
                ir_engine.build_index(documents)
                print("Index built successfully.")
            else:
                print(f"Error loading data: {result.get('message')}")
        else:
            print("No default dataset found. System will start empty.")
    else:
        print(f"System ready with {stats.get('total_documents')} documents.")
        print(f"System ready with {stats.get('total_documents')} documents.")
        
        # Check if index exists on disk
        # Smart Indexing Check
        print("Checking index status...")
        documents = database.get_all_articles()
        
        if ir_engine.check_index_needs_update(documents):
            print("Index missing or outdated. Rebuilding...")
            ir_engine.build_index(documents)
        else:
            print("Index is up to date. Skipping build.")



if __name__ == '__main__':
    print("=" * 60)
    print("News Article Retrieval & Analytics System")
    print("=" * 60)
    
    # Run initialization
    initialize_system()
    
    print("Starting Flask server...")
    print("API will be available at: http://localhost:5000")
    print("")
    print("Endpoints:")
    print("  POST /api/data/load    - Load CSV dataset")
    print("  POST /api/search       - IR search with ranking")
    print("  GET  /api/metrics      - IR metrics")
    print("  POST /api/analytics    - Data mining/analytics")
    print("  GET  /api/live-news    - Live headlines (External API)")
    print("  GET  /api/debug        - Pipeline explanation")
    print("  GET  /api/health       - Health check")
    print("=" * 60)
    
    app.run(debug=True, port=5000)
