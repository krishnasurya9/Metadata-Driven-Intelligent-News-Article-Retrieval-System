import sys
import os
import time

# Ensure backend dir is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import database
    import ir_engine
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

print("Loading documents from database...")
start_time = time.time()
documents = database.get_all_articles()
print(f"Loaded {len(documents)} documents in {time.time() - start_time:.2f}s.")

print("Building index with new parameters (max_features=50000, min_df=1)...")
start_time = time.time()
result = ir_engine.build_index(documents)
print(f"Index built in {time.time() - start_time:.2f}s.")
print("Result:", result)
