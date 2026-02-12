
import pickle
import duckdb
import os
import sys

# Paths
DB_PATH = os.path.join('..', 'data', 'news_corpus.duckdb')
INDEX_PATH = os.path.join('..', 'data', 'tfidf_index.pkl')

print(f"Checking Database at {DB_PATH}...")
try:
    conn = duckdb.connect(DB_PATH)
    count = conn.execute("SELECT COUNT(*) FROM news_articles").fetchone()[0]
    print(f"Total articles: {count}")
    
    sample = conn.execute("SELECT doc_id, title, content FROM news_articles LIMIT 3").fetchall()
    print("\nSample Articles:")
    for row in sample:
        print(f"ID: {row[0]}")
        print(f"Title: {str(row[1])[:50]}...")
        print(f"Content: {str(row[2])[:50]}...")
        print("-" * 30)
    conn.close()
except Exception as e:
    print(f"Database error: {e}")

print(f"\nChecking Index at {INDEX_PATH}...")
if os.path.exists(INDEX_PATH):
    try:
        with open(INDEX_PATH, 'rb') as f:
            data = pickle.load(f)
            vectorizer = data['vectorizer']
            doc_vectors = data['doc_vectors']
            doc_ids = data['doc_ids']
            vocab = data['vocabulary']
            
            print(f"Vectorizer fitted: {hasattr(vectorizer, 'vocabulary_')}")
            print(f"Doc vectors shape: {doc_vectors.shape}")
            print(f"Number of doc IDs: {len(doc_ids)}")
            print(f"Vocabulary size: {len(vocab)}")
            
            # Check for 'jumanji'
            term = "jumanji"
            if term in vocab:
                print(f"'{term}' IS in the vocabulary (ID: {vocab[term]})")
            else:
                print(f"'{term}' is NOT in the vocabulary")
                
            # Check for 'news'
            term = "news"
            if term in vocab:
                print(f"'{term}' IS in the vocabulary (ID: {vocab[term]})")
            else:
                print(f"'{term}' is NOT in the vocabulary")
                
    except Exception as e:
        print(f"Index error: {e}")
else:
    print("Index file not found!")
