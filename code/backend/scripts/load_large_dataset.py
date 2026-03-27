"""
Script to properly ingest and embed the 120,000 articles dataset for Data Mining / IR presentation.
This runs asynchronously so it doesn't crash the Flask backend.
"""

import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database
import ir_engine

def main():
    print("="*60)
    print("   LARGE DATASET INGESTER & INDEXER (120k frozen_corpus)")
    print("="*60)
    
    file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'cdm_data', 'frozen_corpus.csv'))
    
    if not os.path.exists(file_path):
        print(f"[!] Error: Could not find frozen_corpus.csv at {file_path}")
        sys.exit(1)
        
    print(f"[*] Step 1: Loading documents into DuckDB from: {file_path}")
    start = time.time()
    
    # Load into database
    result = database.load_articles_from_csv(file_path, mode='replace')
    
    if result.get('status') == 'error':
        print(f"[!] Database load failed: {result.get('message')}")
        sys.exit(1)
        
    print(f"[+] Loaded {result.get('documents_loaded', 0)} documents in {time.time()-start:.2f}s")
    
    print("\n[*] Step 2: Building BM25 and FAISS Vector indices")
    print("    This process computes semantic embeddings for all documents.")
    print("    Expected time: 10 - 20 minutes (depending on CPU).")
    
    docs = database.get_all_articles()
    
    index_start = time.time()
    index_result = ir_engine.build_index(docs)
    
    if index_result.get('status') == 'error':
        print(f"[!] Index building failed: {index_result.get('message')}")
        sys.exit(1)
        
    print(f"\n[+] Success! Index rebuilt in {time.time() - index_start:.2f}s")
    print(f"    Indexed Documents: {index_result.get('documents_indexed')}")
    print("    Search Engine is now fully operational with the complete dataset.")

if __name__ == '__main__':
    main()
