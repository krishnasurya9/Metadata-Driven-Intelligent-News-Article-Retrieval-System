# Zeroth Review: Project Status & Implementation Report

## 1. Project Overview
**Title:** Metadata-Driven News Article Retrieval & Analytics System
**Goal:** A standalone, offline-capable AI system for Information Retrieval (IR) and Analytics on news articles choices, featuring explainable results and live news integration.

This project combines traditional IR techniques (TF-IDF) with modern metadata-aware ranking and analytics to provide a comprehensive news intelligence tool. It is designed to operate locally (using DuckDB) but can fetch live data (The Guardian API) when connected.

---

## 2. System Architecture

### **Backend (Python/Flask)**
*   **API Server (`app.py`)**: RESTful API endpoints for search, analytics, data loading, and live news.
*   **Database (`database.py`)**: Uses **DuckDB** for high-performance, local analytical queries. Storage of article content and metadata.
*   **IR Engine (`ir_engine.py`)**: Custom implementation of **TF-IDF Vectorization** using `scikit-learn`.
    *   **Features:** Cosine similarity scoring, metadata boosting (recency, category match), and dynamic ranking.
*   **Live News Service (`guardian_service.py`)**: Integration with **The Guardian API** to fetch real-time articles.
*   **LLM Service (`llm_service.py`)**: Interface for local LLMs (Ollama) to provide summaries and explanations (optional integration).

### **Frontend (Vanilla Stack)**
*   **Core**: HTML5, custom CSS3 (Dark/Glassmorphism theme), Vanilla JavaScript.
*   **Modules**:
    *   `ir-mode.js`: Handles search input, result rendering, and interaction.
    *   `analytics-mode.js`: Renders charts (using Chart.js) for trends and distributions.
    *   `live-news.js`: Manages the live news feed and API interactions.
*   **UI/UX**: Responsive sidebar layout, toggleable panels for Metrics and Analytics.

---

## 3. Key Features Implemented

### **A. Information Retrieval (Search) Mode**
*   **Keyword Search**: Full-text search across article titles and content.
*   **Scanning & Ranking**:
    *   Base Score: TF-IDF Cosine Similarity.
    *   **Boosters**:
        *   *Recency*: Newer articles get a score multiplier.
        *   *Title Match*: Exact matches in titles rank higher.
        *   *Category/Source*: Metadata weighting.
*   **Explainability**: "Why this result?" tooltip showing score contributions.

### **B. Analytics Dashboard**
*   **Temporal Trends**: Line charts showing article frequency over time.
*   **Category Distribution**: Pie/Bar charts usage of news categories.
*   **Source Analysis**: Breakdown of articles by publisher.

### **C. Live News Integration**
*   **API Connection**: Real-time fetching from The Guardian.
*   **Data Normalization**: Maps external API fields to internal schema (Title, Body, Thumbnail, etc.).
*   **UI Integration**: Dedicated "Live News" section that seamlessly blends with local results.

### **D. Metrics and Evaluation**
*   **Performance Sidebar**: Users can toggle a sidebar to see IR metrics.
*   **Metrics Tracked**:
    *   *Precision*: Relevance of retrieved results.
    *   *Recall* (Estimated): Coverage of relevant documents.
    *   *F1 Score*: Harmonic mean of Precision and Recall.
*   **Dynamic Calculation**: Metrics update per query based on score distribution heuristics.

---

## 4. Codebase Structure

```text
code/
├── backend/
│   ├── app.py              # Main Entry Point & API Routes
│   ├── database.py         # DuckDB Connection & Validations
│   ├── ir_engine.py        # Search Logic & Ranking Algorithms
│   ├── guardian_service.py # Live News Fetcher
│   ├── analytics_engine.py # Aggregation Logic for Charts
│   └── preprocessor.py     # Text Cleaning (Stopwords, Stemming)
├── frontend/
│   ├── index.html          # Single Page Application Root
│   ├── styles.css          # Global Styles & Animations
│   ├── app.js              # State Management & Routing
│   ├── live-news.js        # Live Feed Controller
│   └── ir-mode.js          # Search Controller
└── data/                   # Storage for CSV datasets & SQLite DB
```

## 5. Recent Work & Status
*   **Refactored Repository**: Cleaned up large files, organized into `backend` and `frontend` directories.
*   **Ranking Fixes**: Solved issues where search scores were zeroing out; optimized vocabulary size and stopword removal.
*   **Live News Added**: Implemented `guardian_service.py` and connected it to the frontend.
*   **Metrics UI**: Added the sliding sidebar for real-time system performance monitoring.

## 6. Pending / Next Steps
*   **Full LLM Integration**: Ensure `llm_service.py` is fully wired up to the frontend for "Generate Summary" buttons.
*   **User Feedback Loop**: Implement simple "Thumbs Up/Down" to capture ground-truth relevance for better metric calculation.
*   **Deployment**: Finalize Dockerfile or startup scripts for easier one-click launch.
