"""
Main Flask API Server for News Intelligence System
"""
import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
from dotenv import load_dotenv
import sys
import traceback
from functools import wraps

# Add the parent code directory to Python path  
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database
import ir_engine
import mining_engine
import analytics_engine
import llm_service
import news_fetcher
import cdm_analytics.preprocessing as cdm_prep
import cdm_analytics.clustering as cdm_clust
import cdm_analytics.classification as cdm_class

load_dotenv()

app = Flask(__name__)
CORS(app)

last_metrics = {"precision": 0.0, "recall": 0.0, "f1": 0.0, "map": 0.0, "average_score": 0.0}

def _cdm_frozen_guard_error():
    """Return a consistent error payload when frozen CDM data is unavailable."""
    status = cdm_prep.get_frozen_corpus_status()
    return jsonify({
        "status": "error",
        "message": "CDM frozen corpus is required and was not found.",
        "data_source": status
    }), 500

def _assert_cdm_frozen_corpus():
    """Hard guard: CDM endpoints must use frozen corpus only."""
    status = cdm_prep.get_frozen_corpus_status()
    print(f"[CDM] Data source locked -> {status['source']} @ {status['path']} (exists={status['exists']})")
    return status["exists"]

# Decorator to run mining_engine on frozen corpus
def with_frozen_corpus(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not _assert_cdm_frozen_corpus():
            return _cdm_frozen_guard_error()
        original = mining_engine._get_data_for_mining
        mining_engine._get_data_for_mining = cdm_prep.load_frozen_data
        try:
            return func(*args, **kwargs)
        finally:
            mining_engine._get_data_for_mining = original
    return wrapper

# ==========================================
# SYSTEM ROUTES
# ==========================================
@app.route('/api/health', methods=['GET'])
def health_check():
    try:
        db_status = database.get_db_status()
        corpus_count = db_status.get("document_count", 0) if db_status.get("status") == "online" else 0
        
        return jsonify({
            "status": "success",
            "data": {
                "index_status": ir_engine.get_index_info(),
                "llm_status": llm_service.get_status(),
                "corpus_count": corpus_count,
                "db_status": db_status,
                "fetch_status": news_fetcher.get_status()
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        return jsonify({"status": "success", "data": database.get_corpus_stats()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/categories', methods=['GET'])
def get_categories():
    try:
        cats = [c['category'] for c in database.execute_query("SELECT DISTINCT category FROM news_articles WHERE category IS NOT NULL")]
        return jsonify({"status": "success", "data": cats})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/sources', methods=['GET'])
def get_sources():
    try:
        srcs = [s['source'] for s in database.execute_query("SELECT DISTINCT source FROM news_articles WHERE source IS NOT NULL")]
        return jsonify({"status": "success", "data": srcs})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/debug', methods=['GET'])
def debug_dump():
    try:
        return jsonify({
            "status": "success",
            "data": {
                "db_stats": database.get_corpus_stats(),
                "index_info": ir_engine.get_index_info(),
                "llm": llm_service.get_status()
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/analytics', methods=['POST'])
def run_analytics():
    """
    Analytics dispatcher used by frontend analytics-mode.js.
    Accepts payload:
      {
        "type": "category_distribution" | "term_frequency" | "source_bias" | "time_trends",
        "doc_ids": [optional list],
        "top_n": 30
      }
    """
    try:
        data = request.json or {}
        analysis_type = (data.get('type') or 'category_distribution').strip().lower()
        doc_ids = data.get('doc_ids')
        top_n = int(data.get('top_n', 30))
        documents = database.get_all_articles()

        if analysis_type == 'category_distribution':
            result = analytics_engine.analyze_category_distribution(documents, doc_ids=doc_ids)
        elif analysis_type == 'term_frequency':
            result = analytics_engine.analyze_term_frequency(documents, doc_ids=doc_ids, top_n=top_n)
        elif analysis_type == 'source_bias':
            result = analytics_engine.analyze_source_bias(documents, doc_ids=doc_ids)
        elif analysis_type == 'time_trends':
            result = analytics_engine.analyze_time_trends(documents, doc_ids=doc_ids)
        else:
            return jsonify({
                "status": "error",
                "message": f"Unsupported analytics type: {analysis_type}"
            }), 400

        return jsonify({"status": "success", "data": result.get("data", result)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ==========================================
# DATA ROUTES
# ==========================================
@app.route('/api/data/load', methods=['POST'])
def load_data():
    try:
        data = request.json or {}
        path = data.get('path', 'news_articles.csv')
        mode = data.get('mode', 'append')
        base_dir = os.path.dirname(__file__)
        full_path = os.path.abspath(os.path.join(base_dir, '..', '..', 'data', path))
        
        if not os.path.exists(full_path):
            # Fallback to cdm_data
            full_path = os.path.abspath(os.path.join(base_dir, '..', '..', 'cdm_data', path))
        
        if not os.path.exists(full_path):
             return jsonify({"status": "error", "message": f"File not found: {path} in data/ or cdm_data/"}), 404
             
        # Before load, track count
        count_before = database.get_corpus_stats().get('total_articles', 0)
        res = database.load_articles_from_csv(full_path, mode=mode)
        count_after = database.get_corpus_stats().get('total_articles', 0)
        
        new_docs_count = count_after - count_before
        
        if count_after > 0:
            if mode == 'append' and count_before > 0 and new_docs_count > 0:
                print(f"Triggering incremental update for {new_docs_count} documents...")
                new_docs = database.execute_query(f"SELECT * FROM news_articles ORDER BY doc_id DESC LIMIT {new_docs_count}")
                threading.Thread(target=ir_engine.update_index, args=(database.get_all_articles(), new_docs)).start()
            else:
                threading.Thread(target=ir_engine.build_index, args=(database.get_all_articles(),)).start()
            
        return jsonify({"status": "success", "data": res, "message": "Triggered index update in background"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/data/upload', methods=['POST'])
def upload_data():
    try:
        if 'file' not in request.files:
            return jsonify({"status": "error", "message": "No file part"}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({"status": "error", "message": "No selected file"}), 400
            
        mode = request.form.get('mode', 'append')
        save_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'cdm_data')
        os.makedirs(save_dir, exist_ok=True)
        path = os.path.join(save_dir, file.filename)
        file.save(path)
        
        count_before = database.get_corpus_stats().get('total_articles', 0)
        res = database.load_articles_from_csv(path, mode=mode)
        count_after = database.get_corpus_stats().get('total_articles', 0)
        new_docs_count = count_after - count_before
        
        if mode == 'append' and count_before > 0 and new_docs_count > 0:
            new_docs = database.execute_query(f"SELECT * FROM news_articles ORDER BY doc_id DESC LIMIT {new_docs_count}")
            threading.Thread(target=ir_engine.update_index, args=(database.get_all_articles(), new_docs)).start()
        else:
            threading.Thread(target=ir_engine.build_index, args=(database.get_all_articles(),)).start()
        
        return jsonify({"status": "success", "data": res})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/data/info', methods=['GET'])
def data_info():
    try:
        stats = database.get_corpus_stats()
        documents = database.get_all_articles()
        # Mocking file list for now
        files = ["news_articles.csv", "frozen_corpus.csv"]
        return jsonify({
            "status": "success",
            "data": {
                "files": files,
                "storage": stats,
                "category_distribution": analytics_engine.analyze_category_distribution(documents).get('data', {})
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/data/load-live', methods=['POST'])
def load_live():
    try:
        news_fetcher.start_background_fetch()
        return jsonify({"status": "success", "message": "Background live fetch started"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/fetch-status', methods=['GET'])
def get_fetch_status():
    try:
        return jsonify({"status": "success", "data": news_fetcher.get_status()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/live-news', methods=['GET'])
def get_live_news():
    try:
        top_news = database.execute_query("SELECT * FROM news_articles ORDER BY doc_id DESC LIMIT 50")
        return jsonify({"status": "success", "data": top_news, "articles": top_news})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ==========================================
# IR SEARCH ROUTES
# ==========================================
@app.route('/api/search', methods=['POST'])
def search():
    global last_metrics
    try:
        print("Received search request.")
        data = request.json or {}
        query = data.get('query', '')
        print(f"Query: {query}")
        if not query:
            return jsonify({"status": "error", "message": "Empty query"}), 400
            
        alpha = float(data.get('alpha', 0.4))
        beta = float(data.get('beta', 0.4))
        gamma = float(data.get('gamma', 0.2))
        boost_recency = data.get('boost_recency', True)
        boost_category = data.get('boost_category', True)
        target_category = data.get('target_category')
        
        print("Fetching all articles for search...")
        docs = database.get_all_articles()
        print(f"Fetched {len(docs)} articles.")
        
        print("Calling ir_engine.search...")
        res = ir_engine.search(query, docs, boost_recency=boost_recency, boost_category=boost_category, 
                               target_category=target_category, alpha=alpha, beta=beta, gamma=gamma)
        print("ir_engine.search completed.")
                               
        if res.get('status') == 'success':
            last_metrics = res.get('metrics', last_metrics)
            # background summary
            if 'top_results' in res and 'bottom_results' in res:
                threading.Thread(target=llm_service.generate_search_summary, args=(query, res.get('top_results'), res.get('bottom_results'))).start()
            
        return jsonify(res)
    except Exception as e:
        print("Error during search:")
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/metrics', methods=['GET'])
def get_last_metrics():
    try:
        return jsonify({"status": "success", "data": last_metrics})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/index/rebuild', methods=['POST'])
def rebuild_index():
    try:
        res = ir_engine.build_index(database.get_all_articles())
        return jsonify({"status": "success", "data": res})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/index/status', methods=['GET'])
def index_status():
    try:
        return jsonify({"status": "success", "data": ir_engine.get_index_info()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ==========================================
# LLM ROUTES
# ==========================================
@app.route('/api/llm/summarize', methods=['POST'])
def llm_summarize():
    try:
        data = request.json or {}
        q = data.get('query', '')
        top = data.get('top_results', [])
        bot = data.get('bottom_results', [])
        summary = llm_service.generate_search_summary(q, top, bot)
        return jsonify({"status": "success", "data": {"summary": summary}})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/llm/status', methods=['GET'])
def llm_status():
    try:
        return jsonify({"status": "success", "data": llm_service.get_status()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ==========================================
# MINING ROUTES — REMOVED (superseded by /api/cdm/* frozen-corpus routes)
# Legacy /api/mining/* endpoints operated on live main DB without frozen-corpus
# decorators and have been replaced. Kept comment for audit trail.
# ==========================================

# ==========================================
# CDM ROUTES (FROZEN CORPUS ONLY)
# ==========================================
@app.route('/api/cdm/datasets', methods=['GET'])
def cdm_datasets():
    try:
        status = cdm_prep.get_frozen_corpus_status()
        return jsonify({
            "status": "success",
            "data": {
                "active_dataset": status.get("dataset"),
                "available_datasets": status.get("available_datasets", {}),
                "active_path": status.get("path"),
                "active_exists": status.get("exists", False)
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/cdm/datasets', methods=['POST'])
def cdm_set_dataset():
    try:
        data = request.json or {}
        dataset = (data.get('dataset') or '').strip().upper()
        if not cdm_prep.set_active_dataset(dataset):
            return jsonify({
                "status": "error",
                "message": "Invalid dataset. Use AG_NEWS or HUFFPOST."
            }), 400

        status = cdm_prep.get_frozen_corpus_status()
        if not status.get("exists"):
            return jsonify({
                "status": "error",
                "message": f"Selected dataset file not found: {status.get('path')}",
                "data": status
            }), 404

        print(f"[CDM] Active dataset switched -> {status.get('dataset')} @ {status.get('path')}")
        return jsonify({"status": "success", "data": status})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/cdm/stats', methods=['GET'])
def cdm_stats():
    try:
        if not _assert_cdm_frozen_corpus():
            return _cdm_frozen_guard_error()
        df = cdm_prep.load_frozen_data()
        res = cdm_prep.get_preprocessing_stats(df)
        return jsonify({"status": "success", "data": res}) if "error" not in res else jsonify({"status": "error", "message": res["error"]}), 500 if "error" in res else 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/cdm/cluster', methods=['POST'])
def cdm_cluster():
    try:
        if not _assert_cdm_frozen_corpus():
            return _cdm_frozen_guard_error()
        data = request.json or {}
        res = cdm_clust.run_clustering(int(data.get('n_clusters', 4)))
        return jsonify({"status": "success", "data": res}) if "error" not in res else jsonify({"status": "error", "message": res["error"]}), 500 if "error" in res else 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/cdm/elbow', methods=['GET'])
def cdm_elbow():
    try:
        if not _assert_cdm_frozen_corpus():
            return _cdm_frozen_guard_error()
        res = cdm_clust.get_elbow_data()
        return jsonify({"status": "success", "data": res}) if "error" not in res else jsonify({"status": "error", "message": res["error"]}), 500 if "error" in res else 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/cdm/classify', methods=['POST'])
def cdm_classify():
    try:
        if not _assert_cdm_frozen_corpus():
            return _cdm_frozen_guard_error()
        res = cdm_class.run_classification()
        return jsonify({"status": "success", "data": res}) if "error" not in res else jsonify({"status": "error", "message": res["error"]}), 500 if "error" in res else 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/cdm/predict', methods=['POST'])
def cdm_predict():
    try:
        if not _assert_cdm_frozen_corpus():
            return _cdm_frozen_guard_error()
        data = request.json or {}
        res = cdm_class.predict_single(data.get('text', ''))
        return jsonify({"status": "success", "data": res}) if "error" not in res else jsonify({"status": "error", "message": res["error"]}), 500 if "error" in res else 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/cdm/pca', methods=['POST'])
@with_frozen_corpus
def cdm_pca():
    """2D PCA scatter data for cluster visualization (CDM-plan: Scatter Plots)."""
    try:
        data = request.json or {}
        n_clusters = int(data.get('n_clusters', 4))
        sample_size = int(data.get('sample_size', 1500))
        res = mining_engine.get_cluster_pca_data(n_clusters=n_clusters, sample_size=sample_size)
        return jsonify({"status": "success", "data": res}) if "error" not in res else jsonify({"status": "error", "message": res["error"]}), 500 if "error" in res else 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/cdm/association', methods=['POST'])
@with_frozen_corpus
def cdm_assoc():
    try:
        data = request.json or {}
        res = mining_engine.generate_association_rules(
            min_support=float(data.get('min_support', 0.01)),
            min_confidence=float(data.get('min_confidence', 0.3)),
            min_lift=float(data.get('min_lift', 1.0))
        )
        return jsonify({"status": "success", "data": res}) if "error" not in res else jsonify({"status": "error", "message": res["error"]}), 500 if "error" in res else 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/cdm/temporal', methods=['POST'])
@with_frozen_corpus
def cdm_temporal():
    try:
        res = mining_engine.analyze_temporal_patterns()
        return jsonify({"status": "success", "data": res}) if "error" not in res else jsonify({"status": "error", "message": res["error"]}), 500 if "error" in res else 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/cdm/keywords', methods=['POST'])
@with_frozen_corpus
def cdm_keywords():
    try:
        data = request.json or {}
        res = mining_engine.analyze_keyword_prominence(int(data.get('top_n', 50)))
        return jsonify({"status": "success", "data": res}) if "error" not in res else jsonify({"status": "error", "message": res["error"]}), 500 if "error" in res else 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def initialize_index():
    ir_engine.check_and_build_index()

if __name__ == '__main__':
    database.init_database()
    initialize_index()
    news_fetcher.start_background_fetch() # Enabled at startup to fetch live news
    app.run(host='0.0.0.0', port=5000, debug=False)