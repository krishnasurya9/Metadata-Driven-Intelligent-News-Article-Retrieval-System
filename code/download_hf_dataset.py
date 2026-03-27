import os
import pandas as pd
from datasets import load_dataset
from datetime import datetime
import random

# Ensure directory exists
cdm_dir = r"a:\MSC\sem 2\project\cdm_data"
os.makedirs(cdm_dir, exist_ok=True)
output_path = os.path.join(cdm_dir, "frozen_corpus.csv")

print("Initializing Hugging Face Dataset Download...")

try:
    # We use AG News as it's a perfect 120k row "large enough" dataset that downloads incredibly fast
    # and has explicit 4-class categorical labels perfect for Clustering/Classification demonstrations.
    print("Fetching 'ag_news' from Hugging Face...")
    dataset = load_dataset("ag_news", split="train")
    
    # Convert to pandas
    df = pd.DataFrame(dataset)
    
    # Map class index to human readable categories
    category_map = {0: "World", 1: "Sports", 2: "Business", 3: "Technology"}
    df['category'] = df['label'].map(category_map)
    df.drop('label', axis=1, inplace=True)
    
    # Generate realistic fake dates for time-series analysis (between 2018 and 2024)
    print("Generating temporal features...")
    start_date = datetime(2018, 1, 1).timestamp()
    end_date = datetime(2024, 1, 1).timestamp()
    
    def random_date(row):
        return pd.to_datetime(random.uniform(start_date, end_date), unit='s').strftime('%Y-%m-%d')
    
    df['published_at'] = df.apply(random_date, axis=1)
    
    # Rename columns to match our expected schema
    df.rename(columns={'text': 'content'}, inplace=True)
    
    # Extract source if possible from text (AG news often starts with "Reuters - " etc)
    print("Extracting journalistic sources...")
    def extract_source(text):
        if " - " in text[:50]:
            return text.split(" - ")[0].strip()
        elif " (Reuters) " in text:
            return "Reuters"
        elif " (AP) " in text:
            return "AP"
        return "Unknown"
        
    df['source'] = df['content'].apply(extract_source)
    
    # Add fake titles (first 10 words of content)
    df['title'] = df['content'].apply(lambda x: ' '.join(x.split()[:10]) + '...')

    # Reorder columns
    df = df[['title', 'content', 'category', 'source', 'published_at']]
    
    # Save to CSV
    print(f"Saving {len(df)} rows to {output_path}...")
    df.to_csv(output_path, index=False, encoding='utf-8')
    print("Success! Frozen corpus is completely ready.")
    
except ImportError:
    print("Error: 'datasets' library not installed. Please run: pip install datasets")
except Exception as e:
    print(f"An error occurred: {e}")
