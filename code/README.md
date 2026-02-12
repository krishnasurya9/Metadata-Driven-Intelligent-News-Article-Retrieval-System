# News Article Retrieval & Analytics System

A standalone, offline AI system for Information Retrieval and Analytics on news articles with explainable results.

## Features

- **IR Mode**: Query-based document retrieval with TF-IDF ranking
- **Analytics Mode**: Data mining and pattern analysis
- **Explainable AI**: Shows why results appear and patterns exist
- **Metadata-aware Boosting**: Recency, category, and tag-based ranking boosts
- **Local LLM Integration**: Optional Ollama for AI-generated summaries

## Project Structure

```
code/
├── backend/
│   ├── app.py              # Flask API server
│   ├── database.py         # DuckDB operations
│   ├── ir_engine.py        # TF-IDF search engine
│   ├── analytics_engine.py # Data mining module
│   ├── llm_service.py      # Ollama integration
│   ├── preprocessor.py     # Text preprocessing
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── index.html          # Main HTML page
│   ├── styles.css          # Dark theme styling
│   ├── app.js              # Core JavaScript
│   ├── ir-mode.js          # Search functionality
│   └── analytics-mode.js   # Analytics charts
└── data/
    └── (place your CSV here)
```

## Quick Start

### 1. Install Dependencies

```bash
cd code/backend
pip install -r requirements.txt
```

### 2. Download a Dataset

Download one of these datasets and save as `code/data/news_articles.csv`:

- **All the News** (Kaggle): ~143k articles
- **AG News**: ~120k articles  
- **BBC News**: ~2,200 articles (lightweight)

### 3. Start the Backend

```bash
cd code/backend
python app.py
```

Server will start at: `http://localhost:5000`

### 4. Load Your Dataset

```bash
# Via API endpoint
curl -X POST http://localhost:5000/api/data/load \
  -H "Content-Type: application/json" \
  -d '{"file_path": "../data/news_articles.csv"}'
```

### 5. Open the Frontend

Open `code/frontend/index.html` in your browser.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/data/load` | POST | Load CSV dataset |
| `/api/search` | POST | IR search with ranking |
| `/api/metrics` | GET | Get IR metrics |
| `/api/analytics` | POST | Run analytics/mining |
| `/api/debug` | GET | Pipeline explanation |
| `/api/categories` | GET | List categories |
| `/api/sources` | GET | List sources |
| `/api/stats` | GET | Corpus statistics |

## Database Schema

```sql
CREATE TABLE news_articles (
  doc_id INTEGER PRIMARY KEY,
  title TEXT,
  content TEXT,
  category TEXT,
  tags TEXT,
  source TEXT,
  published_at DATE,
  word_count INTEGER
);
```

## Technology Stack

- **Backend**: Python, Flask, DuckDB, scikit-learn
- **Frontend**: HTML5, CSS3, JavaScript, Chart.js
- **LLM** (optional): Ollama (llama2, mistral, etc.)

## Offline Operation

This system is designed to work completely offline:
- No internet required after initial setup
- All data stored locally in DuckDB
- Local LLM with Ollama (or fallback rule-based explanations)
