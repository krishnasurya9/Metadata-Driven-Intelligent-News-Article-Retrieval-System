"""
Standalone CLI: python rebuild_index.py
Syncs BM25+FAISS index with current DuckDB state.
Steps: init DB → load all docs → build_index → print result → exit 0/1
"""
import database
import ir_engine
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if __name__ == '__main__':
    print("Initializing Database...")
    database.init_database()
    
    stats = database.get_corpus_stats()
    total = stats.get('total_articles', 0)
    if total == 0:
        print("Database is empty. Nothing to index.")
        sys.exit(0)
        
    print(f"Found {total} documents in database. Building index...")
    result = ir_engine.build_index()
    
    if result.get('status') == 'success':
        print(f"Success! Indexed {result.get('documents_indexed')} documents.")
        sys.exit(0)
    else:
        print(f"Error building index: {result.get('message')}")
        sys.exit(1)
