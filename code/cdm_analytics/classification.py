import pandas as pd
import time
import os
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.svm import LinearSVC
from sklearn.naive_bayes import MultinomialNB
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import LabelEncoder

try:
    from .preprocessing import load_frozen_data
except ImportError:
    from preprocessing import load_frozen_data

MODELS_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'models')
os.makedirs(MODELS_DIR, exist_ok=True)

def run_classification() -> dict:
    """
    Dual classifier benchmark (Naive Bayes vs Linear SVM).
    Uses 10,000 doc stratified sample for speed.
    """
    df = load_frozen_data()
    if df.empty:
        return {"error": "Frozen corpus not found"}
        
    sampled = False
    if len(df) > 10000:
        df = df.sample(n=10000, random_state=42)
        sampled = True
        
    counts = df['category'].value_counts()
    valid_classes = counts[counts >= 5].index
    df = df[df['category'].isin(valid_classes)]
    
    X_text = df['combined_text']
    y = df['category']
    
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)
    classes_list = [str(c) for c in le.classes_]
    
    vectorizer = TfidfVectorizer(max_features=10000, ngram_range=(1,2), sublinear_tf=True)
    X = vectorizer.fit_transform(X_text)
    
    try:
        X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded)
    except:
        X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42)
        
    # Naive Bayes
    t0 = time.time()
    nb = MultinomialNB()
    nb.fit(X_train, y_train)
    nb_time = time.time() - t0
    
    nb_pred = nb.predict(X_test)
    nb_acc = float((nb_pred == y_test).mean())
    nb_report = classification_report(y_test, nb_pred, target_names=classes_list, output_dict=True)
    nb_cm = confusion_matrix(y_test, nb_pred).tolist()
    
    # SVM
    t0 = time.time()
    svm_base = LinearSVC(max_iter=2000, random_state=42)
    svm = CalibratedClassifierCV(svm_base)
    svm.fit(X_train, y_train)
    svm_time = time.time() - t0
    
    svm_pred = svm.predict(X_test)
    svm_acc = float((svm_pred == y_test).mean())
    svm_report = classification_report(y_test, svm_pred, target_names=classes_list, output_dict=True)
    svm_cm = confusion_matrix(y_test, svm_pred).tolist()
    
    # Save SVM model
    joblib.dump(svm, os.path.join(MODELS_DIR, 'cdm_svm.pkl'))
    joblib.dump(vectorizer, os.path.join(MODELS_DIR, 'cdm_tfidf.pkl'))
    joblib.dump(le, os.path.join(MODELS_DIR, 'cdm_le.pkl'))
    
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
        "sampled": sampled,
        "sample_size": len(df) if sampled else None,
        "recommendation": f"{winner} achieved higher accuracy, validating its use as the default classification model."
    }

def predict_single(text: str) -> dict:
    """Predict category for a single article text."""
    clf_path = os.path.join(MODELS_DIR, 'cdm_svm.pkl')
    vec_path = os.path.join(MODELS_DIR, 'cdm_tfidf.pkl')
    le_path = os.path.join(MODELS_DIR, 'cdm_le.pkl')
    
    if not (os.path.exists(clf_path) and os.path.exists(vec_path) and os.path.exists(le_path)):
        # Run classification to generate models on 5k sample first
        run_classification()
        if not os.path.exists(clf_path):
             return {"error": "Failed to train classifier"}
             
    clf = joblib.load(clf_path)
    vectorizer = joblib.load(vec_path)
    le = joblib.load(le_path)
    
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
