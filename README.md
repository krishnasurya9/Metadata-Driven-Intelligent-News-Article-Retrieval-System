# Multi-Objective News Intelligence System

> **A unified architecture serving two distinct academic domains:
> [Information Retrieval (IRT)](#-module-1-information-retrieval--irt) and
> [Computational Data Mining (CDM)](#-module-2-computational-data-mining--cdm).**

This system is split into **two fully independent modules** — you can run either one or both depending on your use case. The live news backend is only required for the IRT module; the CDM Mining Lab works entirely on static, offline datasets.

---

## 🗺️ Choose Your Path

| I want to… | Module | What I need |
|---|---|---|
| Build a **smart search engine** over news articles | ✅ IRT | API keys (optional), Python, `ir_engine.py` |
| Run **data mining algorithms** (clustering, classification, association rules) | ✅ CDM | A dataset CSV/JSON file, `cdm_analytics/` |
| Run **only the CDM backend** (no search, no live news) | ✅ CDM-only | Just 8 packages + dataset file — see below |
| Run **both** for a full academic pipeline | ✅ Both | Full `requirements.txt` |

Jump directly to the section you need:
- **[IRT Module Setup →](#-module-1-information-retrieval--irt)**
- **[CDM Module Setup →](#-module-2-computational-data-mining--cdm)**
- **[CDM Backend Only →](#-cdm-backend-only-lightweight-setup)**
- **[Bringing Your Own Dataset →](#-bringing-your-own-dataset)**

---

## 📦 Common Installation

**Step 1 – Clone the repo**
```bash
git clone https://github.com/krishnasurya9/Metadata-Driven-Intelligent-News-Article-Retrieval-System.git
cd Metadata-Driven-Intelligent-News-Article-Retrieval-System
```

**Step 2 – Install dependencies**
```bash
pip install -r code/backend/requirements.txt
```

---

## 🔍 Module 1: Information Retrieval — IRT

### What is IRT?

The IRT module implements **Metadata-Driven Intelligent News Retrieval** — a hybrid search engine that combines sparse keyword matching with dense semantic understanding to find the most relevant news articles for any query.

### How It Works

| Component | Technology | Role |
|---|---|---|
| **Sparse Retrieval** | BM25 | Exact keyword matching with TF-IDF weighting |
| **Dense Retrieval** | FAISS + `all-MiniLM-L6-v2` | Semantic sentence embedding similarity |
| **Metadata Boosting** | Custom scorer | Recency + Category alignment re-ranking |
| **Explainability** | Local LLM (LM Studio) | Generates natural-language explanations for ranked results |
| **Evaluation** | MAP + Precision-Recall | Algorithmically generated ground-truth benchmarking |

The system merges BM25 and FAISS scores using a configurable formula, then applies a metadata boost layer, giving you a single, explainable ranked result list.

### IRT Setup

1.  **Configure API keys (optional)** – enables live news ingestion from The Guardian, Mediastack, and NewsAPI.  
    Create `code/.env`:
    ```env
    GUARDIAN_API_KEY=your_key_here
    MEDIASTACK_API_KEY=your_key_here
    NEWS_API_KEY=your_key_here
    ```
    > Without API keys, the system starts in offline mode using only pre-indexed articles.

2.  **Start the backend**
    ```bash
    python code/backend/app.py
    ```
    The Flask server starts at `http://localhost:5000`.

3.  **Open the frontend**  
    Open `code/frontend/index.html` in your browser. Use the **Live News** and **Search** panels.

4.  **(Optional) Rebuild search indexes** — required after importing bulk data:
    ```bash
    python code/backend/scripts/rebuild_index.py
    ```

5.  **(Optional) Run IRT evaluation** — generates MAP score and Precision-Recall Curve:
    ```bash
    python code/backend/scripts/evaluate_ir.py
    ```
    Results are saved to `Evaluation_Metrics.md`.

---

## ⛏️ Module 2: Computational Data Mining — CDM

### What is CDM?

The CDM module implements an **Automated Pattern Discovery System** — a self-contained Mining Lab that runs five advanced data mining algorithms on a static "Frozen Corpus". It is **completely independent** from the IRT live pipeline; no API keys or live data are needed.

### What CDM Does

| Algorithm | What It Discovers |
|---|---|
| **Bisecting K-Means + LSA** | Natural topic clusters using TruncatedSVD dimensional reduction. Autonomous Elbow Curve for optimal `K`. |
| **Classification (NB vs. SVM)** | Benchmarks Naive Bayes against Linear SVM on real article categories. |
| **FP-Growth Association Rules** | Mines co-occurring keywords and phrases across the corpus. |
| **Temporal Pattern Mining** | Time-series linear regression to detect trending topics over time. |
| **Keyword Prominence Analysis** | Maps global vs. category-specific vocabulary to identify defining terms. |

### CDM Setup

CDM needs only a dataset file and the backend running. No API keys required.

1.  **Get a dataset** — place it in `cdm_data/` (see [Bringing Your Own Dataset →](#-bringing-your-own-dataset)).  
    Two datasets are included out-of-the-box:

    | File | Description | Size |
    |---|---|---|
    | `cdm_data/frozen_corpus.csv` | **AG News** – 120,000 news articles, 4 categories | ~38 MB |
    | `cdm_data/huffpost_corpus.json` | **HuffPost News** – 210,000 articles, 42 categories | ~83 MB |

2.  **Start the backend** (if not already running):
    ```bash
    python code/backend/app.py
    ```

3.  **Open the Mining Lab UI**  
    Open `code/frontend/index.html` → navigate to the **Mining Lab** tab.

4.  **Switch between datasets at runtime** using the dataset toggle in the Mining Lab header. The active corpus is displayed in the status bar.

5.  **(Optional) Run CDM tests** — verifies all algorithms execute without memory errors:
    ```bash
    python code/test_cdm.py
    ```

---

## 🪶 CDM Backend Only — Lightweight Setup

If you **only want the Mining Lab** (clustering, classification, association rules, etc.) and have no interest in the search engine or live news, you can run a stripped-down version using only a subset of the existing project files.

### What to Take

You only need these files/folders from the repo:

```text
code/
  backend/
    app.py            ← The Flask server (CDM routes live here)
    mining_engine.py  ← Association rules, temporal, keyword, PCA analytics
    preprocessor.py   ← Shared text-cleaning utilities
  cdm_analytics/
    __init__.py
    preprocessing.py  ← Frozen corpus loader & stats
    clustering.py     ← Bisecting K-Means + Elbow Curve
    classification.py ← Naive Bayes vs. SVM benchmarker
cdm_data/
    frozen_corpus.csv      ← AG News dataset (or your own file)
    huffpost_corpus.json   ← HuffPost dataset (optional)
code/frontend/
    index.html        ← Open this in a browser for the Mining Lab UI
    mining-lab.js
    styles.css
    mode-toggle.js
```

> You do **not** need: `ir_engine.py`, `vector_engine.py`, `database.py`, `llm_service.py`, `news_fetcher.py`, or any of the `scripts/` folder.

### What to Install (CDM-only packages)

Instead of the full `requirements.txt`, you only need these 8 packages:

```bash
pip install flask flask-cors scikit-learn nltk pandas numpy mlxtend python-dotenv
```

> **Why fewer packages?** The heavy IRT dependencies (`faiss-cpu`, `sentence-transformers`, `rank_bm25`, `duckdb`) are only needed for the search engine. CDM runs entirely on scikit-learn + pandas.

### Running CDM-Only

Start the same `app.py` — the CDM routes don't depend on IRT being initialized:

```bash
python code/backend/app.py
```

The IRT components (`ir_engine`, `database`, `news_fetcher`) will still try to load. If the heavy packages are not installed they will raise `ImportError`. To avoid that, either:
- Install the full `requirements.txt` (recommended for the complete project), **or**
- Comment out the IRT import lines at the top of `app.py` (lines ~17–22) before running:
  ```python
  # import database
  # import ir_engine
  # import llm_service
  # import news_fetcher
  ```
  Then open `code/frontend/index.html` and go straight to the **Mining Lab** tab — all `/api/cdm/*` endpoints will work normally.

### CDM-Only API Endpoints (no IRT needed)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/cdm/stats` | Dataset statistics (rows, categories, tokens) |
| `GET` | `/api/cdm/datasets` | List available datasets |
| `POST` | `/api/cdm/datasets` | Switch active dataset |
| `POST` | `/api/cdm/cluster` | Run Bisecting K-Means clustering |
| `GET` | `/api/cdm/elbow` | Elbow Curve data for optimal K |
| `POST` | `/api/cdm/classify` | Naive Bayes vs. SVM benchmark |
| `POST` | `/api/cdm/predict` | Predict category of a single text |
| `POST` | `/api/cdm/association` | FP-Growth association rules |
| `POST` | `/api/cdm/temporal` | Temporal trend analysis |
| `POST` | `/api/cdm/keywords` | Keyword prominence analysis |
| `POST` | `/api/cdm/pca` | 2D PCA scatter for cluster visualization |

---

## 📂 Bringing Your Own Dataset

You are not limited to AG News or HuffPost. CDM is designed to accept any structured text dataset. Follow the steps below to plug in a custom corpus.

### Supported Input Formats

| Format | Extension | Required Columns |
|---|---|---|
| CSV (flat file) | `.csv` | `text` (article body), `category` (label), optionally `date` |
| JSON Lines / JSON Array | `.json` | Same as above, in JSON key-value form |
| HuggingFace Dataset | via script | Auto-downloaded and converted to the above format |

### Step-by-Step: Adding a New Dataset

**Step 1 – Prepare your file**

Make sure your dataset has at minimum:
- A **text** column (the article or document body)
- A **category** (or `label`) column for classification

Rename columns if needed to match the schema. Example for CSV:
```csv
text,category,date
"Apple launches new product...","Technology","2024-01-15"
"Election results are in...","Politics","2024-01-16"
```

**Step 2 – Place the file in `cdm_data/`**
```
cdm_data/
  ├── frozen_corpus.csv          ← AG News (built-in)
  ├── huffpost_corpus.json       ← HuffPost (built-in)
  └── my_custom_dataset.csv      ← ← YOUR FILE HERE
```

**Step 3 – Register it in the backend**

Open `code/backend/app.py` and find the `DATASET_REGISTRY` dictionary. Add your dataset:

```python
DATASET_REGISTRY = {
    "agnews": {
        "path": "cdm_data/frozen_corpus.csv",
        "format": "csv",
        "text_col": "text",
        "label_col": "category",
    },
    "huffpost": {
        "path": "cdm_data/huffpost_corpus.json",
        "format": "json",
        "text_col": "headline",
        "label_col": "category",
    },
    # Add your dataset here ↓
    "my_dataset": {
        "path": "cdm_data/my_custom_dataset.csv",
        "format": "csv",
        "text_col": "text",         # column name in your file
        "label_col": "category",    # column name in your file
    },
}
```

**Step 4 – Select it in the UI**  
Restart the backend and use the **Dataset Selector** dropdown in the Mining Lab header to switch to your dataset. All five CDM algorithms will run on it automatically.

### Downloading a HuggingFace Dataset

A helper script is included to download and convert any HuggingFace dataset:
```bash
python code/download_hf_dataset.py --dataset <hf_dataset_name> --split train --output cdm_data/my_dataset.csv
```
Example:
```bash
python code/download_hf_dataset.py --dataset fancyzhx/ag_news --split train --output cdm_data/ag_news_raw.csv
```

---

## 🌟 Recent Updates

*   **Runtime Dataset Switching**: Evaluators can toggle between any registered dataset at runtime — no restart required.
*   **High-Fidelity CDM UI/UX**: Modern, Tavily-inspired design with smooth transitions, custom scrollbars, and interactive loading states.
*   **Architectural Stability**: Resolved BERT model loading warnings; optimized FAISS index initialization to prevent unnecessary rebuilds on startup.
*   **PCA Visualizations**: Fully integrated PCA scatter plots in the Clustering panel for dimensional reduction analytics.
*   **Ablation Studies**: Completed API contract fixes and frontend-backend interaction checks for academic compliance.

---

## 📁 Project Structure

```text
.
├── code/
│   ├── backend/              # Python Flask backend & logic
│   │   ├── app.py            # Main entry point & API Router (DATASET_REGISTRY lives here)
│   │   ├── ir_engine.py      # Hybrid FAISS + BM25 Search (IRT)
│   │   ├── mining_engine.py  # Active corpus CDM analytics
│   │   └── scripts/          # Standalone testing & ingestion utilities
│   │       ├── evaluate_ir.py
│   │       ├── rebuild_index.py
│   │       └── ...
│   ├── cdm_analytics/        # Frozen Corpus specific mining modules
│   │   ├── clustering.py     # Bisecting K-Means + Elbow Curve
│   │   └── classification.py # SVM vs Naive Bayes Benchmarker
│   ├── cdm_data/             # Dataset files (CSV / JSON)
│   │   ├── frozen_corpus.csv     ← AG News (built-in)
│   │   └── huffpost_corpus.json  ← HuffPost (built-in)
│   ├── data/                 # Live DuckDB warehouse and FAISS index bins (IRT)
│   ├── download_hf_dataset.py # HuggingFace dataset downloader utility
│   └── frontend/             # Vanilla HTML/JS frontend (+ Chart.js)
├── ppts/                     # Academic Presentation reports
├── reviews/                  # Grading rubrics and Review printouts
├── Evaluation_Metrics.md     # Auto-generated IRT accuracy report
└── README.md                 # This file
```

---

## 🔗 Key API Endpoints

### IRT Endpoints
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | System health check |
| `POST` | `/api/search` | Hybrid BM25 + FAISS search |
| `GET` | `/api/news` | Fetch recent live news |

### CDM Endpoints
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/cdm/stats` | Active corpus statistics |
| `POST` | `/api/cdm/cluster` | Run Bisecting K-Means |
| `POST` | `/api/cdm/classify` | Run NB vs SVM benchmarking |
| `POST` | `/api/cdm/association` | Run FP-Growth mining |
| `GET` | `/api/cdm/elbow` | Generate Elbow Curve data |
| `POST` | `/api/cdm/switch-dataset` | Switch active corpus at runtime |
