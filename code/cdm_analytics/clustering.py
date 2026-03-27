import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import BisectingKMeans, KMeans
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics import silhouette_score

try:
    from .preprocessing import load_frozen_data
except ImportError:
    from preprocessing import load_frozen_data

def run_clustering(n_clusters=4) -> dict:
    """
    Bisecting K-Means + LSA on frozen corpus.
    Uses a sample of 20,000 for speed if > 20,000 rows.
    """
    df = load_frozen_data()
    if df.empty:
        return {"error": "Frozen corpus not found"}
        
    sampled = False
    sample_size = 20000
    if len(df) > sample_size:
        df = df.sample(n=sample_size, random_state=42).copy()
        sampled = True
        
    vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1,2), sublinear_tf=True)
    X_tfidf = vectorizer.fit_transform(df['combined_text'])
    
    svd = TruncatedSVD(n_components=100, random_state=42)
    X_lsa = svd.fit_transform(X_tfidf)
    
    bkmeans = BisectingKMeans(n_clusters=n_clusters, random_state=42)
    labels = bkmeans.fit_predict(X_lsa)
    df['cluster'] = labels
    
    try:
        sil_score = silhouette_score(X_lsa, labels, sample_size=10000, random_state=42) if len(X_lsa) > 10000 else silhouette_score(X_lsa, labels, random_state=42)
    except:
        sil_score = 0.0
        
    clusters_info = []
    terms = vectorizer.get_feature_names_out()
    outlier_threshold = (len(df) / n_clusters) * 0.3
    weighted_purity = 0
    
    for i in range(n_clusters):
        cluster_mask = (df['cluster'] == i)
        size = int(cluster_mask.sum())
        
        if size == 0: continue
            
        cluster_tfidf = X_tfidf[cluster_mask.values]
        center_tfidf = np.asarray(cluster_tfidf.mean(axis=0)).flatten()
        top_indices = center_tfidf.argsort()[::-1][:15]
        top_terms = [terms[idx] for idx in top_indices]
        
        counts = df.loc[cluster_mask, 'category'].value_counts()
        dominant_cat = counts.index[0] if len(counts) > 0 else "Unknown"
        purity = float(counts.iloc[0]) / size if size > 0 else 0.0
        weighted_purity += (purity * size)
        
        clusters_info.append({
            "cluster_id": i,
            "size": size,
            "percentage": round(size / len(df) * 100, 2),
            "top_terms": list(top_terms),
            "dominant_category": dominant_cat,
            "purity": round(purity, 4),
            "is_outlier_cluster": size < outlier_threshold,
            "sample_titles": df.loc[cluster_mask, 'title'].head(3).tolist()
        })
        
    overall_purity = weighted_purity / len(df) if len(df) > 0 else 0.0
    
    return {
        "method": "Bisecting K-Means + LSA",
        "n_clusters": n_clusters,
        "silhouette_score": round(float(sil_score), 4),
        "clusters": clusters_info,
        "overall_purity": round(overall_purity, 4),
        "sampled": sampled,
        "sample_size": len(df) if sampled else None,
        "interpretation": f"Bisecting K-Means identified {n_clusters} clusters with overall purity {overall_purity:.3f}."
    }

def get_elbow_data(max_k=10) -> dict:
    """
    Compute inertia for k=2 to max_k to generate elbow curve data.
    Uses 5000 doc sample for speed.
    """
    df = load_frozen_data()
    if df.empty:
        return {"error": "Frozen corpus not found"}
        
    if len(df) > 5000:
        df = df.sample(n=5000, random_state=42)
        
    vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
    X = vectorizer.fit_transform(df['combined_text'])
    
    k_values = list(range(2, max_k + 1))
    inertia = []
    
    for k in k_values:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=5)
        kmeans.fit(X)
        inertia.append(float(kmeans.inertia_))
        
    # very simple heuristic for "elbow" point
    diffs = np.diff(inertia)
    second_diffs = np.diff(diffs)
    recommended_k = int(k_values[np.argmax(second_diffs) + 1]) if len(second_diffs) > 0 else 4
    
    return {
        "k_values": k_values,
        "inertia": inertia,
        "recommended_k": recommended_k
    }
