"""
Mining Engine - Advanced Data Mining Algorithms
Implements core data mining functionalities:
1. Association Rule Mining (Keyword co-occurrences)
2. Clustering (K-Means on TF-IDF)
3. Classification (Category prediction)
"""

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import LabelEncoder
import database
import joblib
import os
from collections import Counter
from itertools import combinations

# Global models cache
_models = {
    "kmeans": None,
    "classifier": None,
    "vectorizer": None,
    "label_encoder": None
}

MODELS_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'models')
os.makedirs(MODELS_DIR, exist_ok=True)

def _get_data_for_mining():
    """Fetch data from DB and convert to DataFrame"""
    articles = database.get_all_articles()
    df = pd.DataFrame(articles)
    return df

# =========================================================================
# 1. Association Rule Mining (Simplified for Keywords/Tags)
# =========================================================================

def generate_association_rules(min_support=0.05, min_confidence=0.2):
    """
    Generate association rules between keywords/tags
    Uses a simplified frequent itemset approach to avoid extra dependencies if possible,
    or we can strictly implement Apriori if needed.
    For this 'standalone' demo, a co-occurrence matrix approach is robust and fast.
    """
    df = _get_data_for_mining()
    if df.empty or 'tags' not in df.columns:
        return {"error": "No data available"}

    # 1. Extract transactions (list of tags per article)
    transactions = []
    for tags in df['tags'].dropna():
        # Handle both comma-separated string and list
        if isinstance(tags, str):
            items = [t.strip().lower() for t in tags.split(',') if t.strip()]
        else:
            items = []
        if items:
            transactions.append(sorted(list(set(items)))) # Unique items per transaction

    if not transactions:
        return {"error": "No tags found in data"}

    n_transactions = len(transactions)
    
    # 2. Frequent Itemsets (1-item and 2-item sets)
    item_counts = Counter()
    pair_counts = Counter()

    for trans in transactions:
        for item in trans:
            item_counts[item] += 1
        for pair in combinations(trans, 2):
            pair_counts[pair] += 1

    # Filter by support
    frequent_items = {k: v for k, v in item_counts.items() if (v / n_transactions) >= min_support}
    frequent_pairs = {k: v for k, v in pair_counts.items() if (v / n_transactions) >= min_support}

    # 3. Generate Rules (A -> B)
    rules = []
    for (item_a, item_b), pair_count in frequent_pairs.items():
        # Check Rule A -> B
        support_a = item_counts[item_a]
        confidence_a_b = pair_count / support_a
        
        if confidence_a_b >= min_confidence:
            rules.append({
                "antecedent": item_a,
                "consequent": item_b,
                "support": round(pair_count / n_transactions, 3),
                "confidence": round(confidence_a_b, 3),
                "lift": round(confidence_a_b / (item_counts[item_b] / n_transactions), 3)
            })

        # Check Rule B -> A
        support_b = item_counts[item_b]
        confidence_b_a = pair_count / support_b
        
        if confidence_b_a >= min_confidence:
            rules.append({
                "antecedent": item_b,
                "consequent": item_a,
                "support": round(pair_count / n_transactions, 3),
                "confidence": round(confidence_b_a, 3),
                "lift": round(confidence_b_a / (item_counts[item_a] / n_transactions), 3)
            })

    # Sort by Confidence
    rules.sort(key=lambda x: x['confidence'], reverse=True)
    
    return {
        "transaction_count": n_transactions,
        "rules": rules[:50] # Top 50 rules
    }

# =========================================================================
# 2. Clustering (K-Means)
# =========================================================================

def perform_clustering(n_clusters=5):
    """
    Cluster articles using K-Means on TF-IDF vectors.
    """
    df = _get_data_for_mining()
    if df.empty:
        return {"error": "No data"}

    # Prepare text
    df['combined_text'] = df['title'].fillna('') + " " + df['content'].fillna('')
    
    # Vectorize
    vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
    X = vectorizer.fit_transform(df['combined_text'])
    
    # Cluster
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    kmeans.fit(X)
    
    # Get cluster top terms
    order_centroids = kmeans.cluster_centers_.argsort()[:, ::-1]
    terms = vectorizer.get_feature_names_out()
    
    clusters_info = []
    for i in range(n_clusters):
        top_terms = [terms[ind] for ind in order_centroids[i, :10]]
        
        # Get count
        count = list(kmeans.labels_).count(i)
        
        # Get sample titles
        cluster_indices = [idx for idx, label in enumerate(kmeans.labels_) if label == i]
        sample_titles = df.iloc[cluster_indices[:3]]['title'].tolist()

        clusters_info.append({
            "cluster_id": i,
            "size": count,
            "top_terms": top_terms,
            "samples": sample_titles
        })

    # Find outliers (documents furthest from their cluster center)
    # Simple distance calculation
    # X_dist = kmeans.transform(X)
    # ... (implementation simplified for MVP)

    return {
        "n_clusters": n_clusters,
        "clusters": clusters_info
    }

# =========================================================================
# 3. Classification (Category Prediction)
# =========================================================================

def train_classifier():
    """
    Train a Random Forest classifier to predict category from text.
    Returns evaluation metrics.
    """
    df = _get_data_for_mining()
    if df.empty:
        return {"error": "No data"}
        
    # Filter classes with enough data
    counts = df['category'].value_counts()
    valid_categories = counts[counts >= 5].index
    df = df[df['category'].isin(valid_categories)]
    
    if len(df) < 10:
        return {"error": "Not enough data to train (need at least 10 samples)"}
        
    # Prepare
    df['combined_text'] = df['title'].fillna('') + " " + df['content'].fillna('')
    X_text = df['combined_text']
    y = df['category']
    
    # Vectorize
    vectorizer = TfidfVectorizer(max_features=2000, stop_words='english')
    X = vectorizer.fit_transform(X_text)
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)
    
    # Evaluate
    y_pred = clf.predict(X_test)
    report = classification_report(y_test, y_pred, output_dict=True)
    
    # Save models (optional, for persistent serving)
    # joblib.dump(clf, os.path.join(MODELS_DIR, 'category_classifier.pkl'))
    
    return {
        "accuracy": report['accuracy'],
        "detailed_report": report,
        "classes": list(clf.classes_)
    }
