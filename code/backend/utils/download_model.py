import os
import sys
from sentence_transformers import SentenceTransformer

def download_model():
    print("Attempting to download all-MiniLM-L6-v2...")
    try:
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print("Success! Model downloaded and loaded.")
        
        # Save to local path to be sure?
        # Default cache should be fine if it claims success.
        
    except Exception as e:
        print(f"Download failed: {e}")
        # Try to use a different mirror or method if possible?
        
if __name__ == "__main__":
    download_model()
