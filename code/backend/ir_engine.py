"""
IR Engine Module - Hybrid Information Retrieval
Handles indexing and ranking using BM25 and FAISS (Vector Search)
"""

import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from rank_bm25 import BM25Okapi
import pickle
import os
import time
import json
import datetime
from datetime import datetime as dt

from preprocessor import preprocess_text
import vector_engine
import database

# Global index and data
_bm25: Optional[BM25Okapi] = None
_doc_ids: List[int] = []
_doc_map: Dict[int, int] = {}  # Map doc_id to index

INDEX_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'bm25_index.pkl')
INDEX_META_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'index_meta.json')
LOG_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'index_updates.log')

def log_index_update(message: str):
    """Log index updates to a file"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"
    
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, 'a') as f:
            f.write(log_entry)
        print(f"Logged: {message}")
    except Exception as e:
        print(f"Logging failed: {e}")

def check_index_exists() -> bool:
    """Check if ALL indices and their metadata exist"""
    bm25_exists = os.path.exists(INDEX_PATH) and os.path.getsize(INDEX_PATH) > 0
    vector_exists = os.path.exists(vector_engine.INDEX_PATH) and os.path.getsize(vector_engine.INDEX_PATH) > 0
    bm25_meta_exists = os.path.exists(INDEX_META_PATH) and os.path.getsize(INDEX_META_PATH) > 0
    vector_meta_exists = os.path.exists(vector_engine.META_PATH) and os.path.getsize(vector_engine.META_PATH) > 0
    
    return bm25_exists and vector_exists and bm25_meta_exists and vector_meta_exists

def check_and_build_index():
    """
    Checks if the index needs to be built and builds it if necessary.
    Otherwise, loads the existing index. Handles incremental catching up silently.

    Decision flow:
      1. All 4 artifact files missing → full build.
      2. All 4 exist AND DB has MORE docs than meta → incremental update.
      3. All 4 exist AND counts match (or DB <= indexed) → just load from disk.
      4. If anything above errors → fall back to full build.
    """
    current_count = database.get_corpus_stats().get('total_documents', 0)

    # Step 1: If any index file is missing, we must build from scratch.
    if not check_index_exists():
        print("[IR] Index artifacts missing. Building full index from scratch...")
        documents = database.get_all_articles()
        build_index(documents)
        return

    # Step 2 & 3: All files exist — read meta and decide load vs incremental.
    try:
        with open(INDEX_META_PATH, 'r') as f:
            meta = json.load(f)
        indexed_count = meta.get('doc_count', 0)

        if indexed_count > 0 and current_count > indexed_count:
            # DB has grown since last index → incremental update
            diff = current_count - indexed_count
            print(f"[IR] DB has {diff} new docs since last index. Running incremental update...")
            if load_index():
                new_docs = database.execute_query(
                    f"SELECT * FROM news_articles ORDER BY doc_id DESC LIMIT {diff}"
                )
                new_docs = new_docs[::-1]  # chronological order
                update_index(database.get_all_articles(), new_docs)
            else:
                # load failed unexpectedly, rebuild
                print("[IR] Load failed during incremental path. Rebuilding...")
                build_index(database.get_all_articles())
        else:
            # Index is current (or DB has same/fewer docs) → just load
            print(f"[IR] Index is up to date ({indexed_count} docs). Loading from disk...")
            load_index()

    except Exception as e:
        # Meta read failed for any reason → safe fallback: full rebuild
        print(f"[IR] Could not read index metadata ({e}). Rebuilding full index...")
        build_index(database.get_all_articles())

def _index_needs_update(current_count: int) -> bool:
    """
    Internal helper to check if the index needs to be rebuilt entirely.
    """
    if not os.path.exists(INDEX_META_PATH):
        return True
        
    try:
        with open(INDEX_META_PATH, 'r') as f:
            meta = json.load(f)
            
        indexed_count = meta.get('doc_count', 0)
        
        # If DB is completely out of sync (e.g. wiped or different than index)
        if indexed_count != current_count:
            return True
        return False
        
    except Exception as e:
        return True

def build_index(documents: List[Dict]) -> Dict[str, Any]:
    """
    Build Hybrid Index (BM25 + FAISS)
    """
    global _bm25, _doc_ids, _doc_map
    
    if not documents:
        return {"status": "error", "message": "No documents to index"}
    
    start_time = time.time()
    
    # --- Step 1: Build BM25 Index ---
    log_index_update(f"Starting index build for {len(documents)} documents...")
    print(f"Building BM25 index for {len(documents)} documents...")
    tokenized_corpus = []
    _doc_ids = []
    _doc_map = {}
    
    for idx, doc in enumerate(documents):
        title = doc.get('title', '') or ''
        content = doc.get('content', '') or ''
        text = f"{title} {title} {content}"
        
        processed = preprocess_text(text)
        tokens = processed.split()
        
        tokenized_corpus.append(tokens)
        _doc_ids.append(doc['doc_id'])
        _doc_map[doc['doc_id']] = idx
    
    _bm25 = BM25Okapi(tokenized_corpus)
    
    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
    with open(INDEX_PATH, 'wb') as f:
        pickle.dump({
            'bm25': _bm25,
            'doc_ids': _doc_ids,
            'doc_map': _doc_map
        }, f)
        
    # --- Step 2: Build Vector Index ---
    vector_result = vector_engine.build_index(documents)
    if vector_result.get('status') == 'error':
        log_index_update(f"Vector Index Build Failed: {vector_result.get('message')}")
    else:
        log_index_update(f"Vector Index Built. Status: {vector_result.get('status')}")
    
    # --- Step 3: Save Metadata for Smart Indexing ---
    with open(INDEX_META_PATH, 'w') as f:
        json.dump({
            'doc_count': len(documents),
            'last_built': time.time(),
            'version': '1.0'
        }, f)
    
    duration = time.time() - start_time
    log_index_update(f"Index build completed in {duration:.2f}s. Indexed {len(_doc_ids)} docs.")
    
    return {
        "status": "success",
        "documents_indexed": len(_doc_ids),
        "algorithm": "Hybrid (BM25 + FAISS)",
        "time_taken": f"{duration:.2f}s",
        "vector_status": vector_result
    }

def update_index(all_documents: List[Dict], new_documents: List[Dict]) -> Dict[str, Any]:
    """Incremental update for Hybrid Index handling new documents only for vector encoding"""
    global _bm25, _doc_ids, _doc_map
    
    if not new_documents:
        return {"status": "success"}
        
    if not load_index():
        return build_index(all_documents)
        
    start_time = time.time()
    log_index_update(f"Starting incremental update for {len(new_documents)} new documents...")
    
    # 1. Update Vector Index Incrementally (Solves 1-hour rebuild problem)
    vector_result = vector_engine.update_index(new_documents)
    
    # 2. Rebuild BM25 for all ONLY if adding a massive batch (> 500)
    # Rebuilding BM25 for 120k docs takes ~48 seconds. For live news batches (~200), we skip it!
    # FAISS semantic vector search is 100% updated immediately and will perfectly retrieve these docs.
    if len(new_documents) > 5000:
        print(f"Rebuilding complete BM25 index for {len(all_documents)} documents...")
        tokenized_corpus = []
        _doc_ids = []
        _doc_map = {}
        
        for idx, doc in enumerate(all_documents):
            title = doc.get('title', '') or ''
            content = doc.get('content', '') or ''
            text = f"{title} {title} {content}"
            
            processed = preprocess_text(text)
            tokenized_corpus.append(processed.split())
            _doc_ids.append(doc['doc_id'])
            _doc_map[doc['doc_id']] = idx
            
        from rank_bm25 import BM25Okapi
        _bm25 = BM25Okapi(tokenized_corpus)
        
        with open(INDEX_PATH, 'wb') as f:
            pickle.dump({
                'bm25': _bm25,
                'doc_ids': _doc_ids,
                'doc_map': _doc_map
            }, f)
    else:
        # Just update tracking maps for FAISS compatibility
        print("Live fetch detected (<500). Skipping BM25 rebuild for immediate parallel execution...")
        for doc in new_documents:
            doc_id = doc['doc_id']
            if doc_id not in _doc_ids:
                _doc_ids.append(doc_id)
                _doc_map[doc_id] = len(_doc_ids) - 1
        
        # Save just the updated mappings back to BM25 pickle
        if _bm25 is not None:
             with open(INDEX_PATH, 'wb') as f:
                 pickle.dump({
                     'bm25': _bm25,
                     'doc_ids': _doc_ids,
                     'doc_map': _doc_map
                 }, f)
                 
    with open(INDEX_META_PATH, 'w') as f:
        json.dump({
            'doc_count': len(all_documents),
            'last_built': time.time(),
            'version': '1.0'
        }, f)
        
    duration = time.time() - start_time
    log_index_update(f"Incremental update completed seamlessly in {duration:.2f}s.")
    return {
        "status": "success", 
        "documents_added": len(new_documents),
        "vector_status": vector_result
    }


def load_index() -> bool:
    """Load both indices"""
    global _bm25, _doc_ids, _doc_map
    
    # Load BM25
    if not os.path.exists(INDEX_PATH):
        return False
    
    try:
        with open(INDEX_PATH, 'rb') as f:
            data = pickle.load(f)
            _bm25 = data['bm25']
            _doc_ids = data['doc_ids']
            _doc_map = data.get('doc_map', {})
            
            if not _doc_map and _doc_ids:
                _doc_map = {did: i for i, did in enumerate(_doc_ids)}
    except Exception as e:
        print(f"Error loading BM25 index: {e}")
        return False
        
    # Load Vector Index
    if not vector_engine.load_index():
        print("Warning: Vector index failed to load. Hybrid search may be degraded.")
        
    return True


def search(query: str, documents: List[Dict], filters: Dict = None,
           boost_recency: bool = False, boost_category: bool = False,
           target_category: str = None, top_k: int = 50,
           alpha: float = 0.4, beta: float = 0.4, gamma: float = 0.2) -> Dict[str, Any]:
    """
    Perform Hybrid Search (BM25 + Vector + Meta)
    alpha: Weight for BM25
    beta: Weight for Vector
    gamma: Weight for Metadata
    """
    global _bm25, _doc_ids
    
    if _bm25 is None:
        if not load_index():
            return {"status": "error", "message": "Index not built."}
    
    # 1. BM25 Search
    processed_query = preprocess_text(query)
    query_tokens = processed_query.split()
    
    bm25_scores = {}
    if query_tokens:
        raw_scores = _bm25.get_scores(query_tokens)
        # Normalize BM25 scores (simple max norm)
        max_score = np.max(raw_scores) if len(raw_scores) > 0 and np.max(raw_scores) > 0 else 1.0
        
        for idx, score in enumerate(raw_scores):
            if score > 0:
                doc_id = _doc_ids[idx]
                bm25_scores[doc_id] = float(score) / max_score

    # 2. Vector Search
    vector_results = vector_engine.search(query, top_k=top_k*2) # Get more candidates
    vector_scores = {}
    if vector_results:
        # Vector scores are already cosine similarity (0-1 range approx)
        for res in vector_results:
            vector_scores[res['doc_id']] = res['score']
            
    # 3. Hybrid Fusion
    # Normalized scores are 0-1, so we just weigh them
    
    all_doc_ids = set(bm25_scores.keys()) | set(vector_scores.keys())
    
    final_results = []
    doc_lookup = {d['doc_id']: d for d in documents}
    
    for doc_id in all_doc_ids:
        if doc_id not in doc_lookup:
            continue
            
        doc = doc_lookup[doc_id]
        
        # Apply Filters
        if filters:
            if filters.get('category') and doc.get('category') != filters['category']:
                continue
            if filters.get('source') and doc.get('source') != filters['source']:
                continue
        
        s_bm25 = bm25_scores.get(doc_id, 0.0)
        s_vec = vector_scores.get(doc_id, 0.0)
        
        # Zero-score floor for BM25
        if s_bm25 == 0.0 and s_vec > 0.0:
            s_bm25 = 0.001
            
        # Metadata Score Calculation
        recency_score = 0.1
        pub_at = doc.get('published_at')
        if pub_at:
            try:
                if isinstance(pub_at, str):
                    pub_date = dt.fromisoformat(pub_at.replace('Z', '+00:00')).replace(tzinfo=None)
                elif isinstance(pub_at, datetime.date) and not isinstance(pub_at, datetime.datetime):
                    pub_date = dt.combine(pub_at, dt.min.time())
                else:
                    pub_date = pub_at
                days_old = (dt.now() - pub_date).days
                if days_old <= 30:
                    recency_score = 1.0
                elif days_old <= 90:
                    recency_score = 0.7
                elif days_old <= 365:
                    recency_score = 0.4
            except Exception as e:
                print(f"Error calculating recency for {doc_id}: {e}")
                pass

        category_score = 1.0 if doc.get('category') == target_category else 0.0
        s_meta = (0.6 * recency_score) + (0.4 * category_score)
        
        final_score = (alpha * s_bm25) + (beta * s_vec) + (gamma * s_meta)
            
        final_results.append({
            "doc_id": doc_id,
            "title": doc.get('title', ''),
            "content_excerpt": (doc.get('content', '') or '')[:300] + '...',
            "score": round(final_score, 4),
            "ss_breakdown": {
                "bm25": round(s_bm25, 3),
                "vector": round(s_vec, 3)
            },
            "metadata": {
                "category": doc.get('category'),
                "source": doc.get('source'),
                "published_at": str(doc.get('published_at'))
            }
        })
        
    # Sort
    final_results.sort(key=lambda x: x['score'], reverse=True)
    
    bottom = final_results[-10:] if len(final_results) >= 10 else final_results
    
    metrics = calculate_metrics(final_results, k=top_k)
    
    return {
        "status": "success",
        "query": query,
        "total_results": len(final_results),
        "top_results": final_results[:top_k],
        "bottom_results": bottom,
        "metrics": metrics
    }

def calculate_metrics(results: List[Dict], k: int = 10) -> Dict[str, float]:
    """Calculate metrics for results"""
    if not results:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0, "map": 0.0, "average_score": 0.0}
    
    top_score = results[0]['score'] if results else 0
    relevant_threshold = top_score * 0.5
    
    relevant_in_top_k = sum(1 for r in results[:k] if r['score'] >= relevant_threshold)
    precision_at_k = float(relevant_in_top_k) / k if k > 0 else 0.0
    
    total_relevant_estimated = sum(1 for r in results if r['score'] >= relevant_threshold)
    recall_at_k = float(relevant_in_top_k) / total_relevant_estimated if total_relevant_estimated > 0 else 0.0
    
    f1 = (2 * precision_at_k * recall_at_k) / (precision_at_k + recall_at_k) if (precision_at_k + recall_at_k) > 0 else 0.0
    
    ap_sum = 0.0
    rel_count = 0
    for i, r in enumerate(results[:k], 1):
        if r['score'] >= relevant_threshold:
            rel_count += 1
            ap_sum += rel_count / i
    map_approx = ap_sum / total_relevant_estimated if total_relevant_estimated > 0 else 0.0

    avg_score = sum(r['score'] for r in results[:k]) / len(results[:k]) if results[:k] else 0.0

    return {
        "precision": float(round(precision_at_k, 4)),
        "recall": float(round(recall_at_k, 4)),
        "f1": float(round(f1, 4)),
        "map": float(round(map_approx, 4)),
        "average_score": float(round(avg_score, 4))
    }

def get_index_info() -> Dict[str, Any]:
    """Get info about index"""
    global _bm25, _doc_ids
    
    if _bm25 is None:
        if check_index_exists():
            load_index()
            
    return {
        "status": "ready" if _bm25 else "not_built",
        "documents_indexed": len(_doc_ids) if _doc_ids else 0,
        "algorithm": "Hybrid (BM25 + FAISS)"
    }
