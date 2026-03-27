"""
Mining Engine - Advanced Data Mining Algorithms
Implements core data mining functionalities:
1. Clustering (Bisecting K-Means + LSA)
2. Classification (Naive Bayes vs Linear SVM)
3. Association Rule Mining (FP-Growth on TF-IDF keywords)
4. Temporal Pattern Mining
5. Keyword Prominence Analysis
"""

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import BisectingKMeans
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics import silhouette_score, classification_report, confusion_matrix
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import database
import joblib
import os
import time
from collections import Counter
from scipy.stats import linregress

# For association rules
try:
    from mlxtend.frequent_patterns import fpgrowth, association_rules
except ImportError:
    pass

MODELS_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'models')
os.makedirs(MODELS_DIR, exist_ok=True)

def _get_data_for_mining():
    """Fetch data from DB and convert to DataFrame"""
    articles = database.get_all_articles()
    df = pd.DataFrame(articles)
    return df

# =========================================================================
# 1. Clustering (Bisecting K-Means + LSA)
# =========================================================================

def perform_clustering(n_clusters=4, method='bisecting'):
    """Bisecting K-Means on LSA-reduced TF-IDF space."""
    df = _get_data_for_mining()
    if df.empty:
        return {"error": "No data"}

    df['combined_text'] = df['title'].fillna('') + " " + df['content'].fillna('')
    
    # 1. TF-IDF
    vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1,2), stop_words='english', sublinear_tf=True)
    X_tfidf = vectorizer.fit_transform(df['combined_text'])
    
    # 2. LSA (TruncatedSVD)
    svd = TruncatedSVD(n_components=min(100, X_tfidf.shape[1]-1), random_state=42)
    X_lsa = svd.fit_transform(X_tfidf)
    
    # 3. Bisecting K-Means
    bkmeans = BisectingKMeans(n_clusters=n_clusters, random_state=42)
    labels = bkmeans.fit_predict(X_lsa)
    df['cluster'] = labels
    
    # 4. Silhouette Score
    try:
        if len(set(labels)) > 1:
            # use a sample for speed if dataset is too large
            if len(X_lsa) > 10000:
                sil_score = silhouette_score(X_lsa, labels, sample_size=10000, random_state=42)
            else:
                sil_score = silhouette_score(X_lsa, labels, random_state=42)
        else:
            sil_score = 0.0
    except:
        sil_score = 0.0
        
    # Analyzing Clusters via TF-IDF centers
    # Since we did LSA, we can't easily get original terms from bkmeans.cluster_centers_ (which are in LSA space).
    # We will compute pseudo-centers in TF-IDF space by averaging TF-IDF vectors for each cluster.
    clusters_info = []
    terms = vectorizer.get_feature_names_out()
    outlier_threshold = (len(df) / n_clusters) * 0.3
    
    weighted_purity = 0
    
    for i in range(n_clusters):
        cluster_mask = (df['cluster'] == i)
        size = int(cluster_mask.sum())
        
        if size == 0:
            continue
            
        cluster_tfidf = X_tfidf[cluster_mask]
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
        "interpretation": f"Bisecting K-Means grouped {len(df)} articles into {n_clusters} clusters. Silhouette score is {sil_score:.3f} and overall purity is {overall_purity:.3f}."
    }

# =========================================================================
# 2. Classification (Dual Classifier Benchmark)
# =========================================================================

def train_classifier(classifier='both'):
    """Dual Benchmark: Naive Bayes vs Linear SVM"""
    df = _get_data_for_mining()
    if df.empty:
        return {"error": "No data"}
        
    counts = df['category'].value_counts()
    valid_categories = counts[counts >= 5].index
    df = df[df['category'].isin(valid_categories)]
    
    if len(df) < 10:
        return {"error": "Not enough data to train"}
        
    df['combined_text'] = df['title'].fillna('') + " " + df['content'].fillna('')
    X_text = df['combined_text']
    y = df['category']
    
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)
    
    vectorizer = TfidfVectorizer(max_features=10000, ngram_range=(1,2), stop_words='english', sublinear_tf=True)
    X = vectorizer.fit_transform(X_text)
    
    try:
        X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded)
    except:
        # Fallback if stratify fails
        X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42)
        
    classes_list = [str(c) for c in le.classes_]
    
    # Train Naive Bayes
    t0 = time.time()
    nb = MultinomialNB()
    nb.fit(X_train, y_train)
    nb_time = time.time() - t0
    
    nb_pred = nb.predict(X_test)
    nb_acc = float((nb_pred == y_test).mean())
    nb_report = classification_report(y_test, nb_pred, target_names=classes_list, output_dict=True)
    nb_cm = confusion_matrix(y_test, nb_pred).tolist()
    
    # Train SVM
    t0 = time.time()
    svm_base = LinearSVC(max_iter=2000, random_state=42)
    svm = CalibratedClassifierCV(svm_base)
    svm.fit(X_train, y_train)
    svm_time = time.time() - t0
    
    svm_pred = svm.predict(X_test)
    svm_acc = float((svm_pred == y_test).mean())
    svm_report = classification_report(y_test, svm_pred, target_names=classes_list, output_dict=True)
    svm_cm = confusion_matrix(y_test, svm_pred).tolist()
    
    # Save SVM as it usually wins
    joblib.dump(svm, os.path.join(MODELS_DIR, 'svm_classifier.pkl'))
    joblib.dump(vectorizer, os.path.join(MODELS_DIR, 'tfidf_vectorizer.pkl'))
    joblib.dump(le, os.path.join(MODELS_DIR, 'label_encoder.pkl'))
    
    winner = "SVM" if svm_acc >= nb_acc else "Naive Bayes"
    delta = abs(svm_acc - nb_acc)
    
    return {
        "naive_bayes": {
            "accuracy": nb_acc,
            "training_time_seconds": round(nb_time, 3),
            "classification_report": nb_report,
            "confusion_matrix": nb_cm,
            "classes": classes_list
        },
        "svm": {
            "accuracy": svm_acc,
            "training_time_seconds": round(svm_time, 3),
            "classification_report": svm_report,
            "confusion_matrix": svm_cm,
            "classes": classes_list
        },
        "winner": winner,
        "accuracy_delta": round(delta, 4),
        "dataset_size": len(df),
        "train_size": X_train.shape[0],
        "test_size": X_test.shape[0],
        "recommendation": f"{winner} achieved higher accuracy, validating its use as the default classification model for this text corpus."
    }

def load_classifier():
    clf_path = os.path.join(MODELS_DIR, 'svm_classifier.pkl')
    vec_path = os.path.join(MODELS_DIR, 'tfidf_vectorizer.pkl')
    le_path = os.path.join(MODELS_DIR, 'label_encoder.pkl')
    
    if os.path.exists(clf_path) and os.path.exists(vec_path) and os.path.exists(le_path):
        clf = joblib.load(clf_path)
        vectorizer = joblib.load(vec_path)
        le = joblib.load(le_path)
        return clf, vectorizer, le
    return None, None, None

def predict_category(text: str) -> dict:
    clf, vectorizer, le = load_classifier()
    if not clf:
        return {"error": "Classifier not trained yet."}
        
    X = vectorizer.transform([text])
    pred_idx = clf.predict(X)[0]
    probs = clf.predict_proba(X)[0]
    
    predicted_category = str(le.inverse_transform([pred_idx])[0])
    confidence = float(probs[pred_idx])
    
    all_scores = {str(le.classes_[i]): float(probs[i]) for i in range(len(le.classes_))}
    
    return {
        "predicted_category": predicted_category,
        "confidence": confidence,
        "all_scores": all_scores
    }

# =========================================================================
# 3. Association Rule Mining (FP-Growth on Top TF-IDF Keywords)
# =========================================================================

def generate_association_rules(min_support=0.01, min_confidence=0.3, min_lift=1.0):
    """FP-Growth Association Mining using TF-IDF Top Keywords as transactions."""
    try:
        from mlxtend.frequent_patterns import fpgrowth, association_rules
    except ImportError:
        return {"error": "mlxtend not installed. Run 'pip install mlxtend'"}

    df = _get_data_for_mining()
    if df.empty:
        return {"error": "No data"}
        
    df['combined_text'] = df['title'].fillna('') + " " + df['content'].fillna('')
    vectorizer = TfidfVectorizer(max_features=500, stop_words='english')
    X = vectorizer.fit_transform(df['combined_text'])
    
    terms = np.array(vectorizer.get_feature_names_out())
    transactions = []
    
    # Extract top 5 keywords per document
    for i in range(X.shape[0]):
        row = X[i].toarray()[0]
        top_indices = row.argsort()[-5:][::-1]
        # Only include non-zero terms
        trans = [terms[idx] for idx in top_indices if row[idx] > 0]
        transactions.append(trans)
        
    # Convert to one-hot DataFrame for mlxtend
    from mlxtend.preprocessing import TransactionEncoder
    te = TransactionEncoder()
    te_ary = te.fit(transactions).transform(transactions)
    df_trans = pd.DataFrame(te_ary, columns=te.columns_)
    
    # FP-Growth
    frequent_itemsets = fpgrowth(df_trans, min_support=min_support, use_colnames=True)
    if frequent_itemsets.empty:
        return {"error": "No frequent itemsets found. Lower min_support."}
        
    rules_df = association_rules(frequent_itemsets, metric="confidence", min_threshold=min_confidence)
    if rules_df.empty:
        return {"error": "No rules found. Lower min_confidence."}
        
    rules_df = rules_df[rules_df['lift'] >= min_lift]
    rules_df = rules_df.sort_values(by='lift', ascending=False).head(50)
    
    rules = []
    for _, row in rules_df.iterrows():
        ant = list(row['antecedents'])[0] if isinstance(row['antecedents'], (set, frozenset)) else list(row['antecedents'])
        con = list(row['consequents'])[0] if isinstance(row['consequents'], (set, frozenset)) else list(row['consequents'])
        lift = float(row['lift'])
        strength = "Strong" if lift > 2.0 else "Moderate" if lift > 1.0 else "Weak"
        
        rules.append({
            "antecedent": ant if isinstance(ant, str) else ", ".join(ant),
            "consequent": con if isinstance(con, str) else ", ".join(con),
            "support": round(float(row['support']), 4),
            "confidence": round(float(row['confidence']), 4),
            "lift": round(lift, 4),
            "strength": strength
        })
        
    return {
        "method": "FP-Growth on TF-IDF Keywords",
        "transaction_count": len(transactions),
        "frequent_itemsets_found": len(frequent_itemsets),
        "rules": rules,
        "interpretation": f"Derived {len(rules)} strong association rules from top TF-IDF keywords per document using FP-Growth algorithm."
    }

# =========================================================================
# 4. Temporal Pattern Mining
# =========================================================================

def analyze_temporal_patterns():
    """Time-Series analysis of article volume per quarter per category."""
    df = _get_data_for_mining()
    if df.empty:
        return {"error": "No data"}
        
    df['published_at'] = pd.to_datetime(df['published_at'], errors='coerce')
    df = df.dropna(subset=['published_at', 'category'])
    
    if df.empty:
        return {"error": "No valid dates found in corpus."}
        
    date_min = df['published_at'].min().strftime('%Y-%m-%d')
    date_max = df['published_at'].max().strftime('%Y-%m-%d')
    
    df['Quarter'] = df['published_at'].dt.to_period('Q').astype(str)
    
    pivot = pd.crosstab(df['Quarter'], df['category'])
    
    quarterly_volumes = pivot.to_dict(orient='index')
    
    category_trends = {}
    peak_periods = {}
    
    x = np.arange(len(pivot))
    
    for cat in pivot.columns:
        y = pivot[cat].values
        
        # Peak periods
        top_indices = y.argsort()[-3:][::-1]
        peaks = [pivot.index[i] for i in top_indices if y[i] > 0]
        peak_periods[cat] = peaks
        
        # Linear trend
        if len(y) > 1:
            slope, _, _, _, _ = linregress(x, y)
            direction = "rising" if slope > 0.5 else "declining" if slope < -0.5 else "stable"
            category_trends[str(cat)] = {
                "slope": round(float(slope), 4),
                "direction": direction
            }
        else:
            category_trends[str(cat)] = {"slope": 0.0, "direction": "stable"}
            
    # Cross-Category Correlation
    corr_matrix = pivot.corr()
    cross_corr = {}
    cols = list(pivot.columns)
    for i in range(len(cols)):
        for j in range(i+1, len(cols)):
            c1, c2 = cols[i], cols[j]
            val = corr_matrix.loc[c1, c2]
            if not np.isnan(val):
                cross_corr[f"{c1}_vs_{c2}"] = round(float(val), 4)
                
    return {
        "analysis_type": "temporal_pattern_mining",
        "date_range": {"from": date_min, "to": date_max},
        "quarterly_volumes": quarterly_volumes,
        "category_trends": category_trends,
        "peak_periods": peak_periods,
        "cross_category_correlation": cross_corr,
        "interpretation": "Time-series analysis shows volume fluctuations, directional trends via linear regression, and cross-category correlation over time."
    }

# =========================================================================
# 5. Keyword Prominence Analysis
# =========================================================================

def analyze_keyword_prominence(top_n=50):
    """TF-IDF Keyword analysis globally and per category."""
    df = _get_data_for_mining()
    if df.empty:
        return {"error": "No data"}
        
    df['combined_text'] = df['title'].fillna('') + " " + df['content'].fillna('')
    vectorizer = TfidfVectorizer(max_features=500, stop_words='english')
    X = vectorizer.fit_transform(df['combined_text'])
    terms = np.array(vectorizer.get_feature_names_out())
    
    # Global top terms
    mean_tfidf = np.asarray(X.mean(axis=0)).flatten()
    top_indices = mean_tfidf.argsort()[-top_n:][::-1]
    global_top_terms = [{"term": str(terms[i]), "score": round(float(mean_tfidf[i]), 4)} for i in top_indices]
    
    # Category defining terms
    categories = df['category'].dropna().unique()
    category_defining = {}
    cat_terms_sets = {}
    
    for cat in categories:
        mask = (df['category'] == cat)
        if mask.sum() == 0: continue
        
        cat_X = X[mask]
        cat_mean = np.asarray(cat_X.mean(axis=0)).flatten()
        cat_top_idx = cat_mean.argsort()[-20:][::-1]
        
        cat_terms = [{"term": str(terms[i]), "score": round(float(cat_mean[i]), 4)} for i in cat_top_idx]
        category_defining[str(cat)] = cat_terms
        cat_terms_sets[str(cat)] = set([terms[i] for i in cat_top_idx])
        
    # Cross-category terms (appear in top 20 of 3+ categories)
    term_counts = Counter()
    for cat, term_set in cat_terms_sets.items():
        for term in term_set:
            term_counts[term] += 1
            
    cross_category_terms = [term for term, count in term_counts.items() if count >= 3]
    
    # Vocabulary by year
    df['published_at'] = pd.to_datetime(df['published_at'], errors='coerce')
    vocab_by_year = {}
    
    for year, group in df.groupby(df['published_at'].dt.year):
        if pd.isna(year): continue
        year_text = " ".join(group['combined_text'].tolist())
        # simple split for unique vocab size estimate
        vocab_size = len(set(year_text.lower().split()))
        vocab_by_year[str(int(year))] = vocab_size
        
    return {
        "global_top_terms": global_top_terms,
        "category_defining_terms": category_defining,
        "cross_category_terms": cross_category_terms,
        "vocabulary_by_year": vocab_by_year,
        "interpretation": "Extracted global and per-category prominent keywords using TF-IDF weights, identifying terms that cross category boundaries."
    }
