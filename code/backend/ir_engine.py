"""
IR Engine Module - BM25 based Information Retrieval
Handles indexing and ranking using Okapi BM25 algorithm
"""

import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from rank_bm25 import BM25Okapi
import pickle
import os
import time

from preprocessor import preprocess_text

# Global index and data
_bm25: Optional[BM25Okapi] = None
_doc_ids: List[int] = []
_doc_map: Dict[int, int] = {}  # Map doc_id to index

INDEX_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'bm25_index.pkl')


def build_index(documents: List[Dict]) -> Dict[str, Any]:
    """
    Build BM25 index from documents
    """
    global _bm25, _doc_ids, _doc_map
    
    if not documents:
        return {"status": "error", "message": "No documents to index"}
    
    print(f"Building index for {len(documents)} documents...")
    start_time = time.time()
    
    # Prepare corpus for BM25 (list of list of tokens)
    tokenized_corpus = []
    _doc_ids = []
    _doc_map = {}
    
    for idx, doc in enumerate(documents):
        title = doc.get('title', '') or ''
        content = doc.get('content', '') or ''
        
        # Combine title (weighted) and content
        # We repeat title to give it more weight
        text = f"{title} {title} {content}"
        
        # Preprocess (stemming and stopword removal included)
        processed = preprocess_text(text)
        tokens = processed.split()
        
        tokenized_corpus.append(tokens)
        _doc_ids.append(doc['doc_id'])
        _doc_map[doc['doc_id']] = idx
    
    # Build BM25 object
    _bm25 = BM25Okapi(tokenized_corpus)
    
    # Save index to disk
    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
    with open(INDEX_PATH, 'wb') as f:
        pickle.dump({
            'bm25': _bm25,
            'doc_ids': _doc_ids,
            'doc_map': _doc_map
        }, f)
    
    duration = time.time() - start_time
    
    return {
        "status": "success",
        "documents_indexed": len(_doc_ids),
        "algorithm": "BM25Okapi",
        "time_taken": f"{duration:.2f}s",
        "index_path": INDEX_PATH
    }


def load_index() -> bool:
    """Load index from disk if available"""
    global _bm25, _doc_ids, _doc_map
    
    if not os.path.exists(INDEX_PATH):
        return False
    
    try:
        with open(INDEX_PATH, 'rb') as f:
            data = pickle.load(f)
            _bm25 = data['bm25']
            _doc_ids = data['doc_ids']
            _doc_map = data.get('doc_map', {})
            
            # Rebuild doc_map if missing (backward compatibility)
            if not _doc_map and _doc_ids:
                _doc_map = {did: i for i, did in enumerate(_doc_ids)}
                
        return True
    except Exception as e:
        print(f"Error loading index: {e}")
        return False


def search(query: str, documents: List[Dict], filters: Dict = None,
           boost_recency: bool = False, boost_category: bool = False,
           target_category: str = None, top_k: int = 50) -> Dict[str, Any]:
    """
    Search documents using BM25
    """
    global _bm25, _doc_ids
    
    if _bm25 is None:
        if not load_index():
            return {"status": "error", "message": "Index not built."}
    
    # Preprocess query (same pipeline as docs)
    processed_query = preprocess_text(query)
    query_tokens = processed_query.split()
    
    if not query_tokens:
        return {
            "status": "success",
            "results": [],
            "top_results": [],
            "bottom_results": [],
            "message": "Empty query"
        }
    
    # Get BM25 scores
    scores = _bm25.get_scores(query_tokens)
    
    # Fast filtering of non-zero scores
    # scores is a numpy array
    relevant_indices = np.where(scores > 0)[0]
    
    # Create valid result objects
    results = []
    doc_lookup = {d['doc_id']: d for d in documents}
    
    for idx in relevant_indices:
        score = float(scores[idx])
        doc_id = _doc_ids[idx]
        
        if doc_id not in doc_lookup:
            continue
            
        doc = doc_lookup[doc_id]
        
        # Apply Filters
        if filters:
            if filters.get('category') and doc.get('category') != filters['category']:
                continue
            if filters.get('source') and doc.get('source') != filters['source']:
                continue
        
        # Metadata Boosting
        boost = 0.0
        if boost_category and target_category and doc.get('category') == target_category:
            boost += 1.5  # Significant boost for category match
            
        final_score = score + boost
        
        results.append({
            "doc_id": doc_id,
            "title": doc.get('title', ''),
            "content_excerpt": (doc.get('content', '') or '')[:300] + '...',
            "score": round(final_score, 4),
            "metadata": {
                "category": doc.get('category'),
                "source": doc.get('source'),
                "published_at": str(doc.get('published_at'))
            }
        })
    
    # Sort by score descending
    results.sort(key=lambda x: x['score'], reverse=True)
    
    # Pagination / Limits
    top_results = results[:top_k]
    
    return {
        "status": "success",
        "query": query,
        "total_results": len(results),
        "top_results": top_results,
        "bottom_results": [] # Deprecated but kept for API structure
    }


def calculate_metrics(results: List[Dict], k: int = 20) -> Dict[str, float]:
    """Calculate basic metrics for results"""
    if not results:
        return {"precision_at_k": 0.0, "recall_at_k": 0.0}
    
    # Simple heuristic metrics since we don't have ground truth
    # Assume results with high scores (relative to top) are "relevant"
    top_score = results[0]['score'] if results else 0
    relevant_threshold = top_score * 0.5
    
    relevant_retrieved = sum(1 for r in results[:k] if r['score'] >= relevant_threshold)
    
    return {
        "precision_at_k": round(relevant_retrieved / k, 4),
        "recall_at_k": 1.0, # Placeholder
        "total_results": len(results)
    }


def get_index_info() -> Dict[str, Any]:
    """Get info about index"""
    global _bm25, _doc_ids
    
    if _bm25 is None:
        load_index()
        
    return {
        "status": "ready" if _bm25 else "not_built",
        "documents_indexed": len(_doc_ids) if _doc_ids else 0,
        "algorithm": "BM25Okapi"
    }

