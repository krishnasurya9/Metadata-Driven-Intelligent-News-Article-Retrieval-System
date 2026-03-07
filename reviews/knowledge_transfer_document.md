# Project Knowledge Transfer Document
**Review-1 Preparation Summary**

## 1. PROJECT OVERVIEW
*   **Project Title:** Metadata-Driven Intelligent News Article Retrieval System (also referred to dynamically as the Automated Trend Analysis and Sentiment Mining System).
*   **Problem Statement:** In an era of immense information overload, users struggle to find relevant news, discern critical events from noise, and track evolving narratives or sentiment across global news streams dynamically in real-time.
*   **Motivation:** To build a standalone, offline-capable pipeline that automatically ingests, indexes, and analyzes unstructured news data. It bridges classic Information Retrieval (IR) with robust Data Mining techniques, transitioning raw data into actionable knowledge.
*   **Real-world Use Case:** Media monitoring, brand health evaluation, political sentiment tracking, crisis management, and continuous academic research on public opinion dynamics.
*   **Core Idea of the System:** A hybrid architecture combining a multi-source news ingestion engine with a high-performance IR core (TF-IDF and BM25), backed by embedded analytics and advanced Data Mining modules. This produces highly relevant search features coupled with explanatory metrics via Local LLM insights.

## 2. PROJECT OBJECTIVES
*   Develop a low-latency, multi-source ingestion engine that retrieves news from public APIs and dynamically adapts to raw CSVs using a universal auto-ingest schema.
*   Implement an accurate Information Retrieval system utilizing TF-IDF and BM25 to support metadata-driven, semantic searches.
*   Construct a serverless, standalone architecture relying entirely on lightweight embedded databases (DuckDB) for low-overhead local usage.
*   Integrate sophisticated Data Mining modules capable of classification (SVM), clustering (DBSCAN/K-Means), and association-rule generation (Apriori).
*   Enable transparent system evaluation by presenting core IR metrics (Precision, Recall, F1-Score) to users visually.
*   Achieve an Explainable AI flow via the seamless integration of localized offline LLMs (LM Studio/Ollama).

## 3. SYSTEM DESCRIPTION
The system works end-to-end through a progressive pipeline:
*   **Input:** Live API streams (The Guardian, Mediastack, NewsAPI) managed by a background fetcher, along with bulk historical CSV inputs mapping dynamically to local tables.
*   **Processing Pipeline:** Data is ingested > Cleaned/Tokenized (NLTK) > Stored in the embedded DuckDB instance > Mapped into Vector representations (Sparse TF-IDF / BM25 and Dense Sentence-Transformers).
*   **Models Used:** TF-IDF & BM25 for ranking and retrieval. The mining pipeline encompasses Apriori (Association Rules), DBSCAN/K-Means (Clustering), and SVM (Sentiment Classification).
*   **Output:** Ranked search results annotated with performance metrics, dynamic time-series visualizations of topics, and conversational summaries derived from local LLM interpretation.

## 4. TECHNOLOGY STACK
*   **Programming Languages:** Python 3.x, JavaScript, HTML5, CSS3.
*   **Frameworks:** Flask (Backend REST API), Flask-CORS.
*   **Machine Learning / AI Models:** `scikit-learn` (SVM, K-Means, TF-IDF), `rank_bm25`, NLTK, `sentence-transformers` (Dense Embeddings), `faiss-cpu`. Local LLMs via LM Studio / Ollama (OpenAI-compatible APIs).
*   **APIs:** Guardian API, Mediastack, NewsAPI, Local LM Studio HTTP endpoints.
*   **Libraries:** `duckdb` (Storage), `pandas`, `numpy`, `requests`, `python-dotenv`.
*   **Development Environments:** Embedded offline environment, avoiding heavy managed database infrastructure. 

## 5. DATASET INFORMATION
*   **Dataset Sources:** Synthesized from live APIs alongside large-scale academic datasets like AG News (`ag_news_train.csv`), BBC News (`bbc_news.csv`), and India News Headlines (`india-news-headlines.csv`).
*   **Dataset Type:** Textual news articles with corresponding metadata properties (Headline, Context, Source, Publication Date, Tags, and Category).
*   **Dataset Size:** Ranging from 13 MB up to 285 MB per raw file. The active DuckDB corpus size currently rests comfortably at over 300+ MB representing hundreds of thousands of documents.
*   **Preprocessing Steps:** Semantic normalization including stemming, tokenization, removing stop words, standardizing schema typings via `preprocessor.py`, and handling missing fields (e.g. automatically inferring word counts and sources).
*   **Features Used:** `doc_id`, `title`, `content`, `category`, `tags`, `source`, `published_at`, `word_count`.

## 6. SYSTEM ARCHITECTURE
*   **Data Pipeline:** A low-latency ingestion engine (`news_fetcher.py`) runs asynchronous background threads polling APIs, deduplicating records, and committing them to the DuckDB Data Warehouse. The system features an auto-schema mapper for manual CSV integration.
*   **Model Pipeline:** Raw texts are piped to the `vector_engine.py` and `ir_engine.py`. Dense embeddings and TF-IDF matrixes are generated dynamically and saved to pickled index files.
*   **Training Process:** The `mining_engine.py` runs batch operations against the data warehouse to uncover association rules or process clustering structures (Topic Discovery) across subsets of the total corpus.
*   **Inference Process:** Real-time search queries are vectorized, scored by BM25/Cosine Similarity against the loaded offline indexes, and routed through `llm_service.py` for contextual summarization.
*   **Backend/API Layer:** Python Flask serving decoupled endpoints (`/api/search`, `/api/analytics`, `/api/mining/*`, `/api/data/load`, and system metrics endpoints).
*   **Frontend Interaction:** A modular, static HTML/JS frontend toggling visually between 'IR Mode' and 'Analytics Mode'. Embedded Chart.js dashboards render the system's analytical outputs.

## 7. CURRENT PROJECT STATUS
The project is well past structural conception and is currently mid-implementation.

*   **Completed Components:**
    *   Database Warehouse setup (DuckDB) and primary schema design.
    *   Multi-source live news fetching via Background Threads (Mediastack, Guardian, NewsAPI).
    *   Universal auto-ingest schema mappings allowing complex CSV ingestion on-the-fly.
    *   Core Information Retrieval engine featuring functional BM25 and TF-IDF ranking.
    *   Retrieval evaluation modules generating Precision, Recall, F1 scores, and PR Curves (`evaluate_ir.py`).
    *   Functional Local LLM REST bridge via LM Studio.
*   **Components Currently in Development:**
    *   Front-end Analytics visualization (implementing UI Metrics Sidebar for search performance).
    *   Optimizing search bounds (addressing issues surrounding zero-score irrelevant term rankings and extending vocabulary constraints).
*   **Planned / Future Components:**
    *   Deepening the Data Mining Lab outputs (finalizing unsupervised Topic Discovery via DBSCAN and Sentiment Categorization via SVM).
    *   Advanced Time-series analysis and forecasting views for the frontend.

## 8. IMPLEMENTATION DETAILS
*   **Algorithms & Tooling:** 
    *   `evaluate_ir.py` establishes robust metrics calculations for validating Information Retrieval robustness utilizing synthetic and real queries. 
    *   Indexes (`tfidf_index.pkl`, `bm25_index.pkl`) are serialized directly to disk for fast load times.
*   **Integration Steps:** Because the DB is mutable via the background fetchers or API CSV loader, a separate routine (`rebuild_index.py`) sits at the core of the implementation to synchronize the DuckDB tables with the fast retrieval indices. 
*   **Evaluation Methods:** Continuous metric generation alongside queries calculating Precision & Recall directly to ensure IR quality standards. 

## 9. CHALLENGES OR LIMITATIONS
*   **Index Synchronization:** Bulk data importation creates a temporary discrepancy between the DuckDB source of truth and the pickled Models. The system currently requires explicit index rebuilds (`rebuild_index.py`).
*   **Scalability & Local Constraints:** Operating vast datasets (hundreds of megabytes, pushing into gigabytes of raw text) using heavily memory-dependent algorithms locally creates a performance and processing overhead. Model initialization (such as `sentence-transformers`) is prone to internet latency if HuggingFace downloads fail locally. 
*   **Search Relevancy Tweaks:** Fine-tuning parameters for the IR Engine (e.g. limiting term minimum document frequencies, adjusting matrix capacity) required significant manual interventions to prevent 'Zero Score' responses to obscure queries.

## 10. REVIEW-1 PREPARATION SUMMARY
For the academic Review-1 presentation, the project successfully bridges the gap between massive, unstructured information overload and actionable, real-time intelligence using entirely localized, offline systems. The candidate has firmly established the system architecture, relying on a lightweight DuckDB core and fully automated background api-fetching processes ensuring data is continuously enriched. The Information Retrieval groundwork utilizing BM25 and TF-IDF pipelines, paired with local metric analysis (Precision/Recall outputs), provides a solid baseline. Future focus (for upcoming reviews) shifts deliberately toward capitalizing on this architecture via complex Data Mining implementations—specifically rule association, topic clustering, and sentiment mapping.
