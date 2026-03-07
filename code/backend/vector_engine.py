"""
Vector Engine Module - FAISS based Semantic Search
Handles vector embeddings and similarity search
"""

import os
import numpy as np
import pickle
import faiss
from typing import List, Dict, Any, Tuple, Optional
from sentence_transformers import SentenceTransformer

# Global model and index
_model: Optional[SentenceTransformer] = None
_index: Optional[faiss.IndexFlatIP] = None  # Inner Product (Cosine Similarity for normalized vectors)
_doc_ids: List[int] = []
_doc_map: Dict[int, int] = {}

# Paths
INDEX_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'vector_index.faiss')
META_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'vector_meta.pkl')
MODEL_NAME = 'all-MiniLM-L6-v2'

def get_model() -> Optional[SentenceTransformer]:
    """Lazy load the model"""
    global _model
    if _model is None:
        try:
            print(f"Loading embedding model: {MODEL_NAME}...")
            _model = SentenceTransformer(MODEL_NAME)
        except Exception as e:
            print(f"Error loading model {MODEL_NAME}: {e}")
            print("Vector search will be disabled.")
            return None
    return _model

def build_index(documents: List[Dict]) -> Dict[str, Any]:
    """
    Build FAISS index from documents
    """
    global _index, _doc_ids, _doc_map
    
    if not documents:
        return {"status": "error", "message": "No documents to index"}
    
    print(f"Building vector index for {len(documents)} documents...")
    model = get_model()
    
    if model is None:
        return {"status": "error", "message": "Embedding model not available"}
    
    # Prepare corpus for encoding
    texts = []
    _doc_ids = []
    _doc_map = {}
    
    for idx, doc in enumerate(documents):
        # Enriched text representation
        title = doc.get('title', '') or ''
        content = (doc.get('content', '') or '')[:1000] # Truncate for speed
        category = doc.get('category', 'general')
        source = doc.get('source', 'unknown')
        tags = doc.get('tags', '')
        
        # Format: [CATEGORY] [SOURCE] [TAGS] Title. Content
        enriched_text = f"[{category}] [{source}] "
        if tags:
            enriched_text += f"[{tags}] "
        enriched_text += f"{title}. {content}"
        
        texts.append(enriched_text)
        _doc_ids.append(doc['doc_id'])
        _doc_map[doc['doc_id']] = idx
        
    # Encode texts
    print("Encoding documents...")
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
    
    # Normalize embeddings for Cosine Similarity
    faiss.normalize_L2(embeddings)
    
    # Build FAISS index
    dimension = embeddings.shape[1]
    _index = faiss.IndexFlatIP(dimension)
    _index.add(embeddings)
    
    # Save index and metadata
    print("Saving vector index...")
    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
    faiss.write_index(_index, INDEX_PATH)
    
    with open(META_PATH, 'wb') as f:
        pickle.dump({
            'doc_ids': _doc_ids,
            'doc_map': _doc_map
        }, f)
        
    return {
        "status": "success",
        "documents_indexed": len(_doc_ids),
        "algorithm": "FAISS (FlatIP)",
        "dimension": dimension
    }

def load_index() -> bool:
    """Load index from disk"""
    global _index, _doc_ids, _doc_map
    
    if not os.path.exists(INDEX_PATH) or not os.path.exists(META_PATH):
        return False
        
    try:
        _index = faiss.read_index(INDEX_PATH)
        with open(META_PATH, 'rb') as f:
            data = pickle.load(f)
            _doc_ids = data['doc_ids']
            _doc_map = data['doc_map']
        return True
    except Exception as e:
        print(f"Error loading vector index: {e}")
        return False

def search(query: str, top_k: int = 50) -> List[Dict]:
    """
    Search using vector similarity
    Returns list of {doc_id, score}
    """
    global _index
    
    if _index is None:
        if not load_index():
            return []
            
    model = get_model()
    if model is None:
        return []
    
    # Encode query
    query_vector = model.encode([query], convert_to_numpy=True)
    faiss.normalize_L2(query_vector)
    
    # Search
    scores, indices = _index.search(query_vector, top_k)
    
    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1: continue
        
        # Convert index to doc_id
        if idx < len(_doc_ids):
             results.append({
                 "doc_id": _doc_ids[idx],
                 "score": float(score)
             })
             
    return results

def get_status() -> Dict[str, Any]:
    """Get index status"""
    return {
        "status": "ready" if _index else "not_built",
        "documents_indexed": len(_doc_ids) if _doc_ids else 0
    }
