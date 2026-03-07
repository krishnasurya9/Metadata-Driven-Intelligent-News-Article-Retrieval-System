"""
IR Evaluation Script
Calculates Precision, Recall, F1-Score, and Generates Comparative PR Curve
"""

import sys
import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Ensure backend dir is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import ir_engine
    import database
    import generate_synthetic_data
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

PLOT_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'eval', 'pr_curve.png')

def calculate_average_precision(retrieved_docs, relevant_docs):
    """Calculate Average Precision (AP) for a single query"""
    relevant_set = set(relevant_docs)
    precision_sum = 0
    relevant_count = 0
    
    for i, doc_id in enumerate(retrieved_docs):
        if doc_id in relevant_set:
            relevant_count += 1
            precision_at_i = relevant_count / (i + 1)
            precision_sum += precision_at_i
            
    if not relevant_set:
        return 0.0
        
    return precision_sum / len(relevant_set)

def plot_comparative_pr_curve(results):
    """Generate and save Comparative PR Curve"""
    plt.figure(figsize=(10, 8))
    
    for name, data in results.items():
        if data['recalls'] and data['precisions']:
            # Sort by recall to make a cleaner line
            # We want to plot (Recall, Precision) points
            sorted_pairs = sorted(zip(data['recalls'], data['precisions']))
            recalls = [r for r, p in sorted_pairs]
            precisions = [p for r, p in sorted_pairs]
            
            plt.plot(recalls, precisions, marker='.', linestyle='none', alpha=0.5, label=f'{name} (Points)')
            
            # Try to plot a trend line?
            # For now, scatter is safer as we don't have interpolation logic
            
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title('Precision-Recall Curve Comparison')
    plt.legend()
    plt.grid(True)
    plt.savefig(PLOT_PATH)
    print(f"Comparative PR Curve saved to {PLOT_PATH}")

def evaluate():
    print("--- Starting Comparative Evaluation ---")
    
    # 1. Generate/Load Synthetic Data
    csv_path, gt_path = generate_synthetic_data.generate_data()
    
    # 2. Load Data into Database
    print("Loading synthetic data into database...")
    database.load_articles_from_csv(csv_path)
    
    # 3. Build Index
    print("Building index...")
    documents = database.get_all_articles()
    print(f"Documents to index: {len(documents)}")
    ir_engine.build_index(documents)
    
    # 4. Load Ground Truth
    with open(gt_path, 'r') as f:
        ground_truth = json.load(f)
        
    # Strategies to evaluate
    strategies = {
        "BM25 Only": {"alpha": 1.0, "beta": 0.0},
        "Vector Only": {"alpha": 0.0, "beta": 1.0},
        "Hybrid": {"alpha": 0.4, "beta": 0.6}
    }
    
    all_results = {}
    
    print(f"\nEvaluating {len(ground_truth)} queries across {len(strategies)} strategies...")
    
    for strategy_name, weights in strategies.items():
        print(f"\n--- Testing Strategy: {strategy_name} ---")
        total_precision = 0
        total_recall = 0
        total_f1 = 0
        ap_sum = 0
        
        precisions_list = []
        recalls_list = []
        
        for query, relevant_ids in ground_truth.items():
            # Search with specific weights
            results = ir_engine.search(query, documents, top_k=50, 
                                     alpha=weights['alpha'], beta=weights['beta'])
            
            retrieved_ids = [r['doc_id'] for r in results['top_results']]
            
            # Use strict sets for calculation
            relevant_set = set(relevant_ids)
            relevant_count = len(relevant_set)
            
            # 1. Calculate Standard Metrics at Top-10
            top_10_ids = retrieved_ids[:10]
            top_10_set = set(top_10_ids)
            intersection = len(relevant_set.intersection(top_10_set))
            
            precision = intersection / 10
            recall = intersection / relevant_count if relevant_count > 0 else 0
            f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            ap = calculate_average_precision(retrieved_ids, relevant_ids)
            
            total_precision += precision
            total_recall += recall
            total_f1 += f1
            ap_sum += ap
            
            # 2. Calculate P/R Curve Points (at every rank k)
            found_relevant = 0
            for k, doc_id in enumerate(retrieved_ids, start=1):
                if doc_id in relevant_set:
                    found_relevant += 1
                
                # Point at rank k
                p_k = found_relevant / k
                r_k = found_relevant / relevant_count if relevant_count > 0 else 0
                
                precisions_list.append(p_k)
                recalls_list.append(r_k)
            
        n = len(ground_truth)
        all_results[strategy_name] = {
            "map": ap_sum / n,
            "precision": total_precision / n,
            "recall": total_recall / n,
            "f1": total_f1 / n,
            "precisions": precisions_list,
            "recalls": recalls_list
        }
        
    # Print Comparative Table
    print("\n" + "="*60)
    print(f"{'Strategy':<15} | {'MAP':<8} | {'Precision':<10} | {'Recall':<8} | {'F1-Score':<8}")
    print("-" * 60)
    for name, res in all_results.items():
        print(f"{name:<15} | {res['map']:.4f}   | {res['precision']:.4f}     | {res['recall']:.4f}   | {res['f1']:.4f}")
    print("="*60)
    
    # Generate Plot
    plot_comparative_pr_curve(all_results)

if __name__ == "__main__":
    evaluate()
