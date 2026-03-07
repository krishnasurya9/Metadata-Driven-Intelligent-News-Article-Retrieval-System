"""
Synthetic Data Generator for IR Evaluation
Creates a dataset with clear relevance judgments (Ground Truth)
for testing Precision, Recall, and F1-Score.
"""

import pandas as pd
import json
import os
import random

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'eval')
os.makedirs(DATA_DIR, exist_ok=True)

def generate_data():
    print("Generating synthetic evaluation dataset...")
    
    # define topics and documents
    topics = {
        "AI in Healthcare": [
            "Artificial Intelligence is revolutionizing healthcare diagnostics.",
            "Machine learning models predict patient outcomes in hospitals.",
            "AI algorithms help doctors analyze X-rays and MRI scans.",
            "The future of medicine involves AI-driven personalized treatment.",
            "Neural networks used for early detection of cancer.",
            "Robotic surgery powered by AI improves precision.",
            "AI bots assist patients with scheduling and triage."
        ],
        "Space Exploration": [
            "NASA launches new rover to Mars for soil analysis.",
            "SpaceX successfully lands booster rocket on drone ship.",
            "Astronomers discover new exoplanet in habitable zone.",
            "The James Webb Telescope captures stunning images of reliable galaxies.",
            "Humanity plans to colonize the Moon and Mars by 2050.",
            "Black holes remain one of the biggest mysteries of the universe."
        ],
        "Cooking & Food": [
            "How to bake the perfect chocolate chip cookies.",
            "Top 10 pasta recipes for a quick dinner.",
            "The secret to grilling the perfect steak is temperature control.",
            "Vegetarian lasagna that tastes better than meat version.",
            "Understanding the science of fermentation in bread making.",
            "Best street food markets to visit in Asia."
        ],
        "Sports": [
            "The World Cup final was intense with a penalty shootout.",
            "Basketball playoffs are heating up this season.",
            "Tennis champion announces retirement after 20 years.",
            "Marathon runners break world record in Berlin.",
            "Football team hires new coach to improve strategy.",
            "Olympic games will feature new extreme sports categories."
        ]
    }
    
    articles = []
    doc_id = 1
    ground_truth = {}
    
    # 1. Generate Articles
    for category, docs in topics.items():
        for text in docs:
            articles.append({
                "doc_id": doc_id,
                "title": f"{category} News {random.randint(1, 100)}",
                "content": text,
                "category": category,
                "source": "SyntheticNews",
                "published_at": "2024-01-01"
            })
            
            # Map doc_id to category for easy ground truth creation
            if category not in ground_truth:
                ground_truth[category] = []
            ground_truth[category].append(doc_id)
            
            doc_id += 1
            
    # 2. Add some noise/irrelevant docs
    for i in range(5):
        articles.append({
            "doc_id": doc_id,
            "title": "Random Noise",
            "content": f"This is just random text content {i}.",
            "category": "noise",
            "source": "RandomGenerator",
            "published_at": "2024-01-01"
        })
        doc_id += 1
        
    # 3. Save as CSV for loading into DB
    df = pd.DataFrame(articles)
    csv_path = os.path.join(DATA_DIR, 'synthetic_corpus.csv')
    df.to_csv(csv_path, index=False)
    print(f"Saved {len(articles)} documents to {csv_path}")
    
    # 4. Generate Queries and Ground Truth
    # Query -> List of Relevant Doc IDs
    eval_set = {}
    
    # Queries for 'AI in Healthcare'
    eval_set["AI in hospitals"] = ground_truth["AI in Healthcare"]
    eval_set["Machine learning medicine"] = ground_truth["AI in Healthcare"]
    
    # Queries for 'Space Exploration'
    eval_set["Mars rover mission"] = ground_truth["Space Exploration"]
    eval_set["New planets telescope"] = ground_truth["Space Exploration"]
    
    # Queries for 'Cooking'
    eval_set["Chocolate cookies recipe"] = ground_truth["Cooking & Food"]
    
    # Save Ground Truth
    gt_path = os.path.join(DATA_DIR, 'ground_truth.json')
    with open(gt_path, 'w') as f:
        json.dump(eval_set, f, indent=2)
        
    print(f"Saved {len(eval_set)} queries to {gt_path}")
    return csv_path, gt_path

if __name__ == "__main__":
    generate_data()
