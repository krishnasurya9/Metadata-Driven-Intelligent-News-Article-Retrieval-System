"""
Test Script for IR System
Verifies:
1. Vector Encoding
2. Index Building
3. Smart Indexing Check
4. Hybrid Search
"""

import sys
import os
import time

# Ensure backend dir is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import ir_engine
    import vector_engine
    import database
    import numpy as np
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def test_vector_encoding():
    print("\n--- Testing Vector Encoding ---")
    try:
        model = vector_engine.get_model()
        text = "Artificial Intelligence in Healthcare"
        vector = model.encode([text])
        print(f"Encoded '{text}' -> Vector shape: {vector.shape}")
        
        if vector.shape[1] == 384:
            print("PASS: Vector dimension is correct (384).")
        else:
            print(f"FAIL: Expected 384, got {vector.shape[1]}")
    except Exception as e:
        print(f"FAIL: Encoding error: {e}")

def test_indexing_flow():
    print("\n--- Testing Indexing Flow ---")
    
    # Create dummy documents
    docs = [
        {"doc_id": 1, "title": "AI in Medicine", "content": "AI is changing healthcare.", "category": "health", "source": "MedDaily"},
        {"doc_id": 2, "title": "Python Programming", "content": "Python is great for data science.", "category": "tech", "source": "TechBlog"},
        {"doc_id": 3, "title": "Football World Cup", "content": "The match was intense.", "category": "sports", "source": "SportsNet"}
    ]
    
    # 1. Build Index
    print("Building index...")
    result = ir_engine.build_index(docs)
    print("Build Result:", result.get('status'))
    
    if result.get('status') == 'success':
        print("PASS: Index built successfully.")
    else:
        print("FAIL: Index build failed.")
        
    # 2. Check Smart Indexing (Should be False/Skip)
    print("Checking index status (Expect: Up to date)...")
    needs_update = ir_engine.check_index_needs_update(docs)
    
    if not needs_update:
        print("PASS: Smart indexing correctly identified up-to-date index.")
    else:
        print("FAIL: Smart indexing requested rebuild despite no changes.")
        
    # 3. Simulate Change (Add doc)
    docs.append({"doc_id": 4, "title": "New Doc", "content": "Test content", "category": "test"})
    print("Checking index status after adding doc (Expect: Rebuild)...")
    needs_update = ir_engine.check_index_needs_update(docs)
    
    if needs_update:
        print("PASS: Smart indexing correctly identified change.")
    else:
        print("FAIL: Smart indexing failed to detect change.")

def test_search():
    print("\n--- Testing Hybrid Search ---")
    
    # Use existing index (from previous step)
    # We need to reload the connection/docs to be safe, but we can pass the same docs list if we revert the change
    docs = [
        {"doc_id": 1, "title": "AI in Medicine", "content": "AI is changing healthcare.", "category": "health", "source": "MedDaily"},
        {"doc_id": 2, "title": "Python Programming", "content": "Python is great for data science.", "category": "tech", "source": "TechBlog"},
        {"doc_id": 3, "title": "Football World Cup", "content": "The match was intense.", "category": "sports", "source": "SportsNet"}
    ]
    
    # Rebuild to be sure
    ir_engine.build_index(docs)
    
    # Query: "Health AI" -> Should match doc 1
    query = "Health AI"
    print(f"Query: '{query}'")
    
    results = ir_engine.search(query, docs, top_k=3)
    top_doc = results['top_results'][0] if results['top_results'] else None
    
    if top_doc:
        print(f"Top Result: {top_doc['title']} (Score: {top_doc['score']})")
        if top_doc['doc_id'] == 1:
            print("PASS: Correct document retrieved.")
        else:
            print("FAIL: Incorrect top document.")
            
    # Metadata Search
    print("\nTesting Metadata Enrichment...")
    # Query: "TechBlog" -> Should match doc 2 (Source is TechBlog) even if text doesn't explicitly say it
    query = "TechBlog"
    results = ir_engine.search(query, docs, top_k=3)
    top_doc = results['top_results'][0] if results['top_results'] else None
    
    if top_doc and top_doc['doc_id'] == 2:
        print(f"PASS: Metadata search worked. Found {top_doc['title']} via source.")
    else:
        print(f"FAIL: Metadata search failed. Top: {top_doc}")

if __name__ == "__main__":
    test_vector_encoding()
    test_indexing_flow()
    test_search()
