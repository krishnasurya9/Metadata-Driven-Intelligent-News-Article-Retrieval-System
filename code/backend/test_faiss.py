import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv()

import database
import ir_engine
import vector_engine

def debug_faiss():
    database.init_database()
    docs = database.get_all_articles()
    print(f"Total docs in DB: {len(docs)}")
    
    if ir_engine.check_index_exists():
        ir_engine.load_index()
    else:
        print("Indices do not exist")
        return

    q = "technology"
    print(f"Query: {q}")
    
    # Check FAISS directly
    vec_results = vector_engine.search(q, top_k=5)
    print("FAISS raw results:")
    for r in vec_results:
        print(f"  doc_id: {r['doc_id']}, score: {r['score']}")
        
    res = ir_engine.search(q, docs, alpha=0.4, beta=0.4, gamma=0.2)
    print("\nHybrid Search results (Top 3):")
    for r in res.get('top_results', [])[:3]:
        print(f"  doc_id: {r['doc_id']}, score: {r['score']}, breakdown: {r['ss_breakdown']}")

if __name__ == '__main__':
    debug_faiss()
