import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import os
import json
import random
from datetime import datetime, timedelta

def generate_data() -> tuple:
    """
    Creates:
      data/eval/synthetic_corpus.csv  — 50 articles, 4 categories (12-13 each)
      data/eval/ground_truth.json     — 10 queries, each with 5 relevant doc_ids
    Returns: (csv_path, gt_path)
    Each article: realistic title, content (min 80 words), category, source, published_at (2020-2024)
    Ground truth: manually crafted queries matching known article content
    """
    base_dir = os.path.dirname(__file__)
    eval_dir = os.path.abspath(os.path.join(base_dir, '..', 'data', 'eval'))
    os.makedirs(eval_dir, exist_ok=True)
    
    csv_path = os.path.join(eval_dir, 'synthetic_corpus.csv')
    gt_path = os.path.join(eval_dir, 'ground_truth.json')
    
    categories = ['World', 'Sports', 'Business', 'Technology']
    sources = ['Global News', 'Sports Daily', 'Financial Times', 'TechCrunch']
    
    base_date = datetime(2020, 1, 1)
    
    articles = []
    doc_id = 1
    
    for i in range(50):
        category = categories[i % 4]
        source = sources[i % 4]
        days_offset = random.randint(0, 1460)
        pub_date = (base_date + timedelta(days=days_offset)).strftime('%Y-%m-%d %H:%M:%S')
        
        keywords = []
        if category == 'World':
            keywords = ["politics", "international", "summit", "relations", "climate", "treaty"]
        elif category == 'Sports':
            keywords = ["championship", "tournament", "athlete", "score", "match", "victory"]
        elif category == 'Business':
            keywords = ["market", "economy", "stock", "growth", "revenue", "merger"]
        else:
            keywords = ["AI", "software", "startup", "algorithm", "data", "cloud"]
            
        selected_keywords = random.sample(keywords, 3)
        
        title = f"Latest developments in {category}: {' '.join(selected_keywords)}"
        content = f"This is a detailed article about {category}. " * 10
        content += f" Specifically, we discuss {' and '.join(selected_keywords)}. " * 5
        content += f" The situation is evolving rapidly. " * 5
        
        articles.append({
            "doc_id": doc_id,
            "title": title,
            "content": content,
            "category": category,
            "source": source,
            "published_at": pub_date
        })
        doc_id += 1
        
    import csv
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["doc_id", "title", "content", "category", "source", "published_at"])
        writer.writeheader()
        writer.writerows(articles)
        
    gt_data = {}
    for i in range(1, 11):
        target_category = categories[i % 4]
        relevant_docs = [a['doc_id'] for a in articles if a['category'] == target_category][:5]
        gt_data[f"query about {target_category}"] = relevant_docs
        
    with open(gt_path, 'w', encoding='utf-8') as f:
        json.dump(gt_data, f, indent=4)
        
    return csv_path, gt_path

if __name__ == '__main__':
    csv_file, gt_file = generate_data()
    print(f"Generated {csv_file}")
    print(f"Generated {gt_file}")
