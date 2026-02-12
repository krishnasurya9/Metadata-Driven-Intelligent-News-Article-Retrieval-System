# Metadata-Driven Intelligent News Article Retrieval System

A comprehensive news retrieval and analytics system that fetches live news from multiple sources, indexes them for search, and provides analytical insights.

## 🚀 Features

*   **Multi-Source News Fetching**: Integrates with Guardian API, Mediastack, and NewsAPI to fetch live news.
*   **Intelligent Search**: Uses TF-IDF and BM25 algorithms for relevant article retrieval.
*   **Metadata-Driven**: Filters and ranks based on metadata like date, category, and source.
*   **Local Storage**: Uses DuckDB for efficient, local, serverless data storage.
*   **Background Processing**: Automatic background fetching and indexing without blocking the UI.

### 🧪 Advanced Features (In Development)
*   **Analytics Dashboard**: Visualizes new category distributions, source trends, and publication timelines.
*   **Data Mining Lab**:
    *   **Association Rule Mining**: Discovering relationships between keywords.
    *   **Clustering**: Unsupervised topic discovery.
    *   **Classification**: Automated category prediction.


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
    Create a `.env` file in `code/` with your API keys:
    ```env
    GUARDIAN_API_KEY=your_key_here
    MEDIASTACK_API_KEY=your_key_here
    NEWS_API_KEY=your_key_here
    ```

4.  **Run the Application**
    ```bash
    python code/backend/app.py
    ```
    Access the web interface at `http://localhost:5000`.

## 📊 Data Integration & Ingestion

The system supports two primary methods for data ingestion:

### 1. Live News Fetching (Automatic)
The system is designed to automatically fetch news in the background when the application starts.
- **Mechanism**: `news_fetcher.py` runs a background thread that queries configured APIs.
- **Sources**:
    - **The Guardian**: Requires `GUARDIAN_API_KEY`.
    - **Mediastack**: Requires `MEDIASTACK_API_KEY`. Supports multiple keys (`MEDIASTACK_API_KEY_1`, etc.) for higher volume.
    - **NewsAPI**: Requires `NEWS_API_KEY`.
- **Storage**: Fetched articles are deduplicated (by URL/title) and stored in `code/data/news_corpus.duckdb`.

### 2. CSV Bulk Import (Manual)
You can import historical data from CSV files.
- **File Format**: CSV file should have headers like `headline`, `content`, `date`, `category`, `source`.
- **How to Import**:
    1. Place your CSV file in a known location.
    2. Use the `database.load_articles_from_csv(file_path)` function via a Python script or console.
    3. Run `rebuild_index.py` to update the search index.

### 3. Rebuilding the Index
If you manually modify the database or import bulk data, you **must** rebuild the search index:
```bash
python code/backend/rebuild_index.py
```
This script:
1. Loads all documents from DuckDB.
2. Re-calculates TF-IDF and BM25 scores.
3. Saves the updated indices to `code/data/*.pkl`.

## 📁 Project Structure

```
.
├── code/
│   ├── backend/          # Python Flask backend & logic
│   │   ├── app.py        # Main entry point
│   │   ├── database.py   # DuckDB interactions
│   │   ├── ir_engine.py  # Search algorithms
│   │   └── ...
│   ├── frontend/         # Static HTML/JS frontend
│   │   ├── index.html
│   │   └── ...
│   └── data/             # Data storage (indices, DB)
├── plan/                 # Project planning docs
└── README.md             # This file
```
