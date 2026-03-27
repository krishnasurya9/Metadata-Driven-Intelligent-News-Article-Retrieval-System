# Multi-Objective News Intelligence System

> **A unified architecture serving two distinct academic domains: Information Retrieval Techniques (IRT) and Concepts of Data Mining (CDM).**

This repository houses a comprehensive, offline-first AI pipeline that ingests digital news from multiple sources, indexes them for hybrid semantic search, and autonomously discovers underlying correlations and patterns using advanced machine learning models.

---

## 🚀 Core Methodologies

### 🔍 Information Retrieval (IRT) Objective: *Metadata-Driven Intelligent News Retrieval*
*   **Hybrid Search Formula:** Integrates native Sparse retrieval (BM25) with Dense semantic embeddings (FAISS via `all-MiniLM-L6-v2`) and a configurable Metadata boosting algorithm (Recency + Category alignment).
*   **Zero-Score Scaling:** Intelligently floors `0.0` BM25 scores to prevent vector-multiplier penalties when resolving purely semantic queries.
*   **Mathematical Evaluation:** Features a robust evaluation pipeline (`evaluate_ir.py`) generating synthetic ground-truth targets to algorithmically plot Precision-Recall Curves and calculate Mean Average Precision (MAP).
*   **Explainable RAG:** Uses local Language Models (via LM Studio on Port 1234) as post-retrieval synthesizers to explain *why* specific documents ranked highly.

### ⛏️ Data Mining (CDM) Objective: *Automated Pattern Discovery System*
The "Mining Lab" utilizes a 120,000-document *Frozen Corpus* (AG News) to ensure replicable academic benchmarks, implementing 5 advanced algorithms:
*   **Embedded Warehousing:** Operates a local DuckDB data warehouse to unify raw CSVs and live API streams seamlessly.
*   **Bisecting K-Means + LSA Clustering:** Utilizes TruncatedSVD for dimensional reduction on high-dimensional TF-IDF vectors, featuring an autonomous Elbow Curve generation endpoint for optimal `K` discovery.
*   **Classification Benchmarking:** A Dual-Model pipeline evaluating **Naive Bayes** vs. **Linear SVM** via real-time training, emitting complete classification matrices and interactive confusion grids.
*   **FP-Growth Association Rules:** Eliminates sparse tag limitations by mining association rules strictly from the top TF-IDF unigrams/bigrams per document.
*   **Advanced Analytics:** Introduces **Temporal Pattern Mining** (Time-Series linear regression) and **Keyword Prominence Analysis** (Global vs. Category-defining vocabulary mapping).

---

## 🛠️ Setup & Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/krishnasurya9/Metadata-Driven-Intelligent-News-Article-Retrieval-System.git
    cd Metadata-Driven-Intelligent-News-Article-Retrieval-System
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r code/backend/requirements.txt
    ```

3.  **Environment Configuration**
    Create a `.env` file in `code/backend/` with your API keys (optional, but triggers live data streams):
    ```env
    GUARDIAN_API_KEY=your_key_here
    MEDIASTACK_API_KEY=your_key_here
    NEWS_API_KEY=your_key_here
    ```

4.  **Run the Application**
    ```bash
    python code/backend/app.py
    ```
    Access the dynamic web interface at `http://localhost:5000/api/health`. Open `code/frontend/index.html` in your browser.

---

## 📊 Data Integration & Evaluation

### 1. Live News Fetching
If API keys are detected, `app.py` triggers `news_fetcher.py`. This spawns a background thread querying The Guardian, Mediastack, and NewsAPI, automatically ingesting and indexing live text into the unified DuckDB warehouse.

### 2. Manual Data Ingestion & Rebuilding
If you import bulk historical data, you **must** sync the FAISS and BM25 indices:
```bash
python code/backend/scripts/rebuild_index.py
```

### 3. Evaluating System Accuracy (IRT)
Showcase the mathematical rigor of the search engine by running the synthetic evaluation pipeline:
```bash
python code/backend/scripts/evaluate_ir.py
```
This will compile the `Evaluation_Metrics.md` report and generate a Precision-Recall Curve Plot.

### 4. Testing CDM Algorithms
To verify that the offline K-Means and SVM classifiers map correctly to the 120k Frozen Corpus without crashing memory limits:
```bash
python code/test_cdm.py
```

---

## 📁 Project Structure

```text
.
├── code/
│   ├── backend/          # Python Flask backend & logic
│   │   ├── app.py        # Main entry point & API Router
│   │   ├── ir_engine.py  # Hybrid FAISS + BM25 Search
│   │   ├── mining_engine.py # Active corpus CDM analytics
│   │   └── scripts/      # Standalone testing & ingestion utilities
│   │       ├── evaluate_ir.py
│   │       ├── rebuild_index.py
│   │       └── ...
│   ├── cdm_analytics/    # Frozen Corpus specific mining modules
│   │   ├── clustering.py # Bisecting K-Means + Elbow 
│   │   └── classification.py # SVM vs NB Benchmarker
│   ├── cdm_data/         # Houses frozen_corpus.csv (AG News)
│   ├── data/             # Live DuckDB warehouse and FAISS bins
│   └── frontend/         # Vanilla HTML/JS frontend (+ Chart.js)
├── ppts/                 # Academic Presentation reports
├── reviews/              # Grading rubrics and Review printouts
├── Evaluation_Metrics.md # Auto-generated system accuracy report
└── README.md             # This file
```
