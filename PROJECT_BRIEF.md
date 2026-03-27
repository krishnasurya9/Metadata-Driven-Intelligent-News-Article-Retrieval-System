# Comprehensive Project Brief
**Project Title:** Metadata-Driven Intelligent News Article Retrieval System (Automated Trend Analysis and Sentiment Mining System)

## 1. PROJECT OVERVIEW
*   **Name of the project:** Metadata-Driven Intelligent News Article Retrieval System
*   **Main Goal/Purpose:** To build a standalone, offline-capable AI pipeline that automatically ingests digital news from multiple sources, indexes them for semantic search, and autonomously discovers underlying correlations and patterns. It bridges classic Information Retrieval (IR) with robust Data Mining (CDM) techniques.
*   **Problem it is solving:** In an era of immense information overload, users struggle to find relevant news, discern critical events from noise, and track evolving narratives or sentiment across global news streams dynamically in real-time. Standard keyword searches often fail to capture contextual meaning. This system overcomes that by utilizing TF-IDF and BM25 algorithms, alongside metadata weighting (recency, source authority).

## 2. CURRENT STATUS
*   **Fully Completed:**
    *   Database Warehouse setup (DuckDB) and primary schema design.
    *   Multi-source live news fetching via Background Threads (Mediastack, Guardian, NewsAPI).
    *   Universal auto-ingest schema mappings allowing complex CSV ingestion on-the-fly.
    *   Core Information Retrieval engine featuring functional BM25 and TF-IDF ranking.
    *   Retrieval evaluation modules generating Precision, Recall, F1 scores, and PR Curves.
    *   Functional Local LLM REST bridge via LM Studio for explainable AI summaries.
    *   Frontend static layout and routing for IR and Analytics modes.
*   **Partially Done / In Progress:**
    *   Front-end Analytics visualization (implementing UI Metrics Sidebar for search performance).
    *   Optimizing search bounds (addressing issues surrounding zero-score irrelevant term rankings and extending vocabulary constraints).
    *   Refining Data Mining Lab outputs (implementing K-Means clustering, SVM classification, and Apriori association rules on the frontend).
*   **Not Started Yet (Planned):**
    *   Advanced Time-series analysis and forecasting views for the frontend.
    *   Possible optimization of the index synchronization process to be real-time rather than requiring bulk manual rebuilds.

## 3. TECH STACK
*   **Programming Languages:** Python 3.x (Backend), JavaScript, HTML5, Vanilla CSS3 (Frontend).
*   **Frameworks & Libraries:** 
    *   *Backend Framework:* Flask (REST API), Flask-CORS
    *   *Data Storage:* DuckDB
    *   *Machine Learning & NLP:* `scikit-learn`, `nltk`, `pandas`, `numpy`, `rank_bm25`, `sentence-transformers`, `faiss-cpu`.
    *   *Local LLM Integration:* LM Studio / Ollama (OpenAI-compatible APIs)
    *   *Other Utilities:* `requests`, `python-dotenv`
*   **Platform:** Web-based (Local Desktop environment). Operates as a serverless, standalone offline architecture relying on embedded databases to avoid heavy managed infrastructure.

## 4. FILE STRUCTURE
### Backend (`code/backend/`)
*   **`app.py`**: The main Flask application entry point. Defines all REST API endpoints for search, metrics, analytics, and data mining, and initializes the background fetcher.
*   **`database.py`**: Handles all interactions with the DuckDB warehouse (schema creation, data ingestion, querying, and stats generation).
*   **`ir_engine.py`**: The core Information Retrieval logic implementing BM25 (lexical exact match) and TF-IDF/FAISS (semantic search) and calculating evaluation metrics.
*   **`vector_engine.py`**: Handles dense embedding generation and builds/searches vectors using `sentence-transformers` and FAISS.
*   **`analytics_engine.py`**: Processes corpus-level and result-level analysis (category distribution, term frequencies, source biases, time trends).
*   **`mining_engine.py`**: Contains advanced data mining algorithms (Apriori for association rules, K-Means for clustering, SVM for classification).
*   **`llm_service.py`**: Manages the integration with the local LLM (via LM Studio) to generate contextual summaries of search results.
*   **`news_fetcher.py`**: Runs a background asynchronous thread that orchestrates live fetching from configured news APIs.
*   **`guardian_service.py`**: Dedicated API handler for fetching news from The Guardian API.
*   **`mediastack_service.py`**: Dedicated API handler for fetching news from the Mediastack API (supports fallback keys for higher volume).
*   **`preprocessor.py`**: Standardizes text data by lowering casing, tokenizing, stemming, and removing stopwords via NLTK.
*   **`evaluate_ir.py`**: A standalone evaluation script for generating synthetic queries and calculating precision, recall, and F1-scores.
*   **`download_hf_dataset.py`**: Utility script to download large datasets from HuggingFace.
*   **`inspect_data.py`**: Utility to quickly inspect the shape and columns of raw CSV files.
*   **`requirements.txt`**: Python dependencies list.

### CDM Analytics Module (`code/cdm_analytics/`)
*   **`preprocessing.py`**: Specific data cleaning and formatting logic targeted at the frozen dataset used for the CDM review.
*   **`clustering.py`**: Runs K-Means clustering specifically on the frozen dataset.
*   **`classification.py`**: Handles SVM/Naive Bayes training pipeline for the frozen data.

### Frontend (`code/frontend/`)
*   **`index.html`**: The main and only HTML interface. Contains the structure for the search bar, results, metrics panel, and the Analytics dashboard.
*   **`app.js`**: Core frontend logic orchestrating API calls to backend search endpoints and rendering results.
*   **`ir-mode.js`**: Specific frontend logic for handling the standard Information Retrieval UI workflow.
*   **`analytics-mode.js`**: Handles charting and rendering logic for the primary Analytics dashboard.
*   **`live-news.js`**: Controls the live background news ticker/fetching display on the UI.
*   **`mining-lab.js`**: Drives the UI interactions for the advanced K-Means, SVM, and Apriori rule generation features.
*   **`mode-toggle.js`**: Handles the UX toggle switching between IR Mode and Analytics/Mining Mode.
*   **`styles.css`**: All styling attributes for a modern, responsive user interface.

### Data Storage (`code/data/` / Generated Files)
*   **`news_corpus.duckdb`**: The primary embedded database file containing all scraped and loaded articles.
*   **`news_articles.csv`**: Fallback/default bulk import CSV file.
*   **`*.pkl`**: Pickled serialized index files (e.g., `bm25_index.pkl`, `tfidf_index.pkl`) for rapid in-memory searching.

## 5. HOW IT WORKS (LOGIC & FLOW)
1.  **Ingestion & Warehousing:** Upon starting `app.py`, `news_fetcher.py` kicks off background threads to fetch live data from The Guardian, Mediastack, and NewsAPI. Alternatively, manual CSVs can be imported via `/api/data/load`. Data is cleaned by `preprocessor.py` and stored in a local `duckdb` database via `database.py`.
2.  **Indexing:** The raw text base is processed by `ir_engine.py` and `vector_engine.py` to create lexical (BM25) and dense (FAISS) spatial indices. These are serialized to disk (`.pkl`) for high speed retrieval.
3.  **Search & Retrieval (IR):** A user submits a query from the frontend which hits `app.py`. The backend routes the query to `ir_engine.py`, performs a hybrid search (Vector + Lexical), applies metadata boosting (recency/source authority), and returns top/bottom results alongside Precision/Recall metrics.
4.  **Generative AI Explainability:** Ranked results are mapped through `llm_service.py` connected to a local LM Studio instance to generate a human-readable summarization explaining *why* the articles answered the user's query.
5.  **Analytics & Data Mining (CDM):** Users can toggle to "Analytics Mode" (hitting `analytics_engine.py` and `mining_engine.py`). Here, unsupervised algorithms scan the DuckDB subsets to produce categorized clusters, term frequency charts, and discover association rules, rendered visually via Chart.js on the frontend.

## 6. KNOWN BUGS & ISSUES
*   **Index Synchronization:** Bulk data importation creates a temporary discrepancy between the DuckDB source of truth and the pickled Models. The system currently requires explicit index rebuilds (`rebuild_index.py` - currently missing in the backend root but referenced in docs) when large CSVs are ingested.
*   **Memory Overhead & Model Init:** Operating vast datasets locally using memory-heavy algorithms (`sentence-transformers`) can cause huge RAM spikes. If internet drops during initial HuggingFace model download, it faults.
*   **Search Relevancy Tweaks (Zero Score Errors):** Heavily restrictive term frequency params can sometimes cause 'Zero Score' responses to obscure queries, necessitating manual tuning of IR engine thresholds.

## 7. DEPENDENCIES & SETUP
**Prerequisites:** 
*   Python 3.10+
*   Node.js/Live Server (Optional for frontend viewing)
*   LM Studio installed locally and running an OpenAI-compatible server on port 1234 (Recommended Model: Llama 3 or Mistral).

**Setup Steps:**
1.  Navigate into the project repository.
2.  Install Python dependencies: `pip install -r code/backend/requirements.txt`
3.  Create a `.env` file in the `code/backend/` directory with the following keys:
    ```
    GUARDIAN_API_KEY=your_key_here
    MEDIASTACK_API_KEY=your_key_here
    NEWS_API_KEY=your_key_here
    ```
4.  Launch the backend: `python code/backend/app.py`
5.  Open `code/frontend/index.html` in your browser or run it via a simple HTTP server (the backend runs on `http://localhost:5000`).
6.  *Optional but Critical:* Open LM Studio, load your preferred LLM, and start the local server on `http://localhost:1234/v1`.

## 8. ANYTHING ELSE (IMPORTANT NOTES)
*   **Dual-Objective Codebase:** Keep in mind that this codebase is being actively reviewed for two separate academic modules: Information Retrieval Techniques (IRT) and Concepts of Data Mining (CDM). Enhancements should not overwhelmingly skew the architecture away from one or the other.
*   **Offline-First Methodology:** The core philosophy of this project is localized, serverless operation. Do not introduce heavy cloud databases (like AWS RDS or Pinecone) as it violates the embedded nature of the DuckDB+Pickled Index design.
*   **Frozen Dataset Consideration:** The `cdm_analytics` folder operates heavily on a specific "frozen dataset" (`cdm_data/frozen_corpus.csv`) strictly for reviewing classification and clustering performance repeatability. Modifications to `app.py` routing around `/api/cdm/*` should be careful not to break this hardcoded integration.
