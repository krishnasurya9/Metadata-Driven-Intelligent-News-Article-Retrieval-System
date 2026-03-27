"""
Main Flask API Server for News Intelligence System
"""
import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
from dotenv import load_dotenv

import database
import ir_engine
import mining_engine
import analytics_engine
import llm_service
from news_fetcher import NewsFetcher
import cdm_analytics.preprocessing as cdm_prep
import cdm_analytics.clustering as cdm_clust
import cdm_analytics.classification as cdm_class

load_dotenv()

app = Flask(__name__)
CORS(app)

news_fetcher = NewsFetcher()
last_metrics = {"precision": 0.0, "recall": 0.0, "f1": 0.0, "map": 0.0, "average_score": 0.0}

# Decorator to run mining_engine on frozen corpus
def with_frozen_corpus(func):
    def wrapper(*args, **kwargs):
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
        return jsonify({
            "status": "success",
            "data": {
                "index_status": ir_engine.get_index_info(),
                "llm_status": llm_service.get_status(),
                "corpus_count": database.get_corpus_stats().get("total_articles", 0),
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
        cats = [c['category'] for c in database.execute_query("SELECT DISTINCT category FROM articles WHERE category IS NOT NULL")]
        return jsonify({"status": "success", "data": cats})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/sources', methods=['GET'])
def get_sources():
    try:
        srcs = [s['source'] for s in database.execute_query("SELECT DISTINCT source FROM articles WHERE source IS NOT NULL")]
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
        full_path = os.path.abspath(os.path.join(base_dir, '..', 'data', path))
        
        if not os.path.exists(full_path):
             return jsonify({"status": "error", "message": f"File not found: {full_path}"}), 404
             
        res = database.load_articles_from_csv(full_path, mode=mode)
        
        if database.get_corpus_stats().get('total_articles', 0) > 0:
            threading.Thread(target=ir_engine.build_index).start()
            
        return jsonify({"status": "success", "data": res, "message": "Triggered index rebuild in background"})
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
        save_dir = os.path.join(os.path.dirname(__file__), '..', 'cdm_data')
        os.makedirs(save_dir, exist_ok=True)
        path = os.path.join(save_dir, file.filename)
        file.save(path)
        
        res = database.load_articles_from_csv(path, mode=mode)
        threading.Thread(target=ir_engine.build_index).start()
        
        return jsonify({"status": "success", "data": res})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/data/info', methods=['GET'])
def data_info():
    try:
        stats = database.get_corpus_stats()
        # Mocking file list for now
        files = ["news_articles.csv", "frozen_corpus.csv"]
        return jsonify({
            "status": "success",
            "data": {
                "files": files,
                "storage": stats,
                "category_distribution": analytics_engine.analyze_category_distribution().get('data', {})
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
        top_news = database.execute_query("SELECT * FROM articles ORDER BY published_at DESC LIMIT 50")
        return jsonify({"status": "success", "data": top_news})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ==========================================
# IR SEARCH ROUTES
# ==========================================
@app.route('/api/search', methods=['POST'])
def search():
    global last_metrics
    try:
        data = request.json or {}
        query = data.get('query', '')
        if not query:
            return jsonify({"status": "error", "message": "Empty query"}), 400
            
        alpha = float(data.get('alpha', 0.4))
        beta = float(data.get('beta', 0.4))
        gamma = float(data.get('gamma', 0.2))
        boost_recency = data.get('boost_recency', True)
        boost_category = data.get('boost_category', True)
        target_category = data.get('target_category')
        
        docs = database.get_all_articles()
        res = ir_engine.search(query, docs, boost_recency=boost_recency, boost_category=boost_category, 
                               target_category=target_category, alpha=alpha, beta=beta, gamma=gamma)
                               
        if res['status'] == 'success':
            last_metrics = res['metrics']
            # background summary
            threading.Thread(target=llm_service.generate_search_summary, args=(query, res['results'], res['bottom_results'])).start()
            
        return jsonify(res)
    except Exception as e:
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
        res = ir_engine.build_index()
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
# MINING ROUTES (MAIN DB)
# ==========================================
@app.route('/api/mining/cluster', methods=['POST'])
def mining_cluster():
    try:
        data = request.json or {}
        n = int(data.get('n_clusters', 4))
        res = mining_engine.perform_clustering(n)
        return jsonify({"status": "success", "data": res}) if "error" not in res else jsonify({"status": "error", "message": res["error"]}), 500 if "error" in res else 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/mining/classify', methods=['POST'])
def mining_classify():
    try:
        res = mining_engine.train_classifier()
        return jsonify({"status": "success", "data": res}) if "error" not in res else jsonify({"status": "error", "message": res["error"]}), 500 if "error" in res else 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/mining/association', methods=['POST'])
def mining_assoc():
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

@app.route('/api/mining/temporal', methods=['POST'])
def mining_temporal():
    try:
        res = mining_engine.analyze_temporal_patterns()
        return jsonify({"status": "success", "data": res}) if "error" not in res else jsonify({"status": "error", "message": res["error"]}), 500 if "error" in res else 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/mining/keywords', methods=['POST'])
def mining_keywords():
    try:
        data = request.json or {}
        res = mining_engine.analyze_keyword_prominence(int(data.get('top_n', 50)))
        return jsonify({"status": "success", "data": res}) if "error" not in res else jsonify({"status": "error", "message": res["error"]}), 500 if "error" in res else 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/mining/predict', methods=['POST'])
def mining_predict():
    try:
        data = request.json or {}
        res = mining_engine.predict_category(data.get('text', ''))
        return jsonify({"status": "success", "data": res}) if "error" not in res else jsonify({"status": "error", "message": res["error"]}), 500 if "error" in res else 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ==========================================
# ANALYTICS ROUTES (MAIN DB)
# ==========================================
@app.route('/api/analytics', methods=['POST'])
def do_analytics():
    try:
        data = request.json or {}
        atype = data.get('type')
        if atype == 'category_distribution': res = analytics_engine.analyze_category_distribution()
        elif atype == 'term_frequency': res = analytics_engine.analyze_term_frequency(data.get('category'), data.get('top_n', 20))
        elif atype == 'entity_extraction': res = analytics_engine.extract_entities(data.get('text',''))
        elif atype == 'source_bias': res = analytics_engine.analyze_source_bias(data.get('topic'))
        elif atype == 'time_series': res = analytics_engine.analyze_time_series(data.get('category'), data.get('interval', 'M'))
        else: return jsonify({"status": "error", "message": "Invalid analytics type"}), 400
        return jsonify(res)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ==========================================
# CDM ROUTES (FROZEN CORPUS ONLY)
# ==========================================
@app.route('/api/cdm/stats', methods=['GET'])
def cdm_stats():
    try:
        df = cdm_prep.load_frozen_data()
        res = cdm_prep.get_preprocessing_stats(df)
        return jsonify({"status": "success", "data": res}) if "error" not in res else jsonify({"status": "error", "message": res["error"]}), 500 if "error" in res else 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/cdm/cluster', methods=['POST'])
def cdm_cluster():
    try:
        data = request.json or {}
        res = cdm_clust.run_clustering(int(data.get('n_clusters', 4)))
        return jsonify({"status": "success", "data": res}) if "error" not in res else jsonify({"status": "error", "message": res["error"]}), 500 if "error" in res else 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/cdm/elbow', methods=['GET'])
def cdm_elbow():
    try:
        res = cdm_clust.get_elbow_data()
        return jsonify({"status": "success", "data": res}) if "error" not in res else jsonify({"status": "error", "message": res["error"]}), 500 if "error" in res else 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/cdm/classify', methods=['POST'])
def cdm_classify():
    try:
        res = cdm_class.run_classification()
        return jsonify({"status": "success", "data": res}) if "error" not in res else jsonify({"status": "error", "message": res["error"]}), 500 if "error" in res else 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/cdm/predict', methods=['POST'])
def cdm_predict():
    try:
        data = request.json or {}
        res = cdm_class.predict_single(data.get('text', ''))
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

if __name__ == '__main__':
    database.init_database()
    ir_engine.load_index()
    if any([os.getenv('GUARDIAN_API_KEY'), os.getenv('MEDIASTACK_API_KEY'), os.getenv('NEWS_API_KEY')]):
        news_fetcher.start_background_fetch()
    app.run(host='0.0.0.0', port=5000, debug=False)
