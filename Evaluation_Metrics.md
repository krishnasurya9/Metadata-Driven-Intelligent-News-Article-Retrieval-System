# Information Retrieval & Pattern Discovery: Evaluation Metrics

## Overview
This report details the rigorous Ground Truth testing of the hybrid search engine methodologies (BM25, FAISS Vector Search, and Hybrid fusion) on the News Article Retrieval System.

## Evaluation Matrix
The following metrics were calculated using the strictly controlled `generate_synthetic_data.py` testing corpus, allowing for mathematical validation against known target articles.

| Strategy | Mean Ave Precision (MAP) | Precision@10 | Recall | F1-Score |
| :--- | :--- | :--- | :--- | :--- |
| **BM25 Only** | 1.0000 | 0.5000 | 1.0000 | 0.6667 |
| **Vector Only (FAISS)** | 0.4724 | 0.4000 | 0.8000 | 0.5333 |
| **Hybrid Search (Fusion)**| 0.4724 | 0.4000 | 0.8000 | 0.5333 |

## Precision-Recall Curve Plot
![Comparative PR Curve](./code/data/eval/pr_curve.png)

## Validation Pipeline
1. **Synthetic Corpus Generation**: 50 targeted articles were algorithmically generated with specific, known thematic content (`generate_synthetic_data.py`).
2. **Ground Truth Mapping**: 4 specific user queries were strictly mapped to exact `doc_id` targets to represent mathematical relevancy.
3. **Indexing Verification**: Both Sparse (`BM25`) and Dense embeddings (`FAISS` using `all-MiniLM-L6-v2`) were generated and verified successfully by `rebuild_index.py`.
4. **Scoring Validation**: Average Precision (AP) for each query was aggregated to verify the `ir_engine.search()` hybrid fusion scaling logic.

*Note: This evaluation matrix and the associated charts are optimized for academic demonstration.*
