# Metadata-Driven News Article Retrieval & Analytics System
## Implementation Plan

A standalone offline AI system combining Information Retrieval (IR) and Analytics/Data Mining for news articles, with explainable results using RAG + local LLM.

---

## Architecture

```mermaid
graph TB
    subgraph Frontend["Frontend (Static HTML/JS/CSS)"]
        UI[Mode Switch UI]
        IR_UI[IR Mode Interface]
        AN_UI[Analytics Mode Interface]
    end
    
    subgraph Backend["Backend (Python Flask)"]
        API[REST API Endpoints]
        IRE[IR Engine - TF-IDF]
        ANA[Analytics Engine]
        MIN[Mining Engine (New)]
        LLM[Local LLM - LM Studio/Ollama]
    end
    
    subgraph Data["Data Layer"]
        DB[(DuckDB - news_corpus.duckdb)]
        IDX[TF-IDF Index]
    end
    
    UI --> IR_UI
    UI --> AN_UI
    IR_UI --> API
    AN_UI --> API
    API --> IRE
    API --> ANA
    API --> MIN
    IRE --> DB
    ANA --> DB
    MIN --> DB
    IRE --> IDX
    API --> LLM

```

---

## Database Schema (DuckDB - No Installation Required)

DuckDB is an embedded database (like SQLite) - installed via `pip install duckdb`.

### Table: `news_articles`

| Column | Type | Description |
|--------|------|-------------|
| `doc_id` | INTEGER PRIMARY KEY | Unique document identifier |
| `title` | TEXT | Article title |
| `content` | TEXT | Full article content |
| `category` | TEXT | Category (politics, sports, tech, etc.) |
| `tags` | TEXT | Comma-separated keywords |
| `source` | TEXT | News source/publisher |
| `published_at` | DATE | Publication date |
| `word_count` | INTEGER | Word count of content |

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | System health check |
| `/api/data/load` | POST | Load CSV dataset into DuckDB |
| `/api/search` | POST | IR search with TF-IDF ranking |
| `/api/metrics` | GET | Precision, Recall, F1 scores |
| `/api/analytics` | POST | Category, term, source, time analysis |
| `/api/mining/association` | GET | Generate keyword association rules |
| `/api/mining/clustering` | GET | Perform K-Means clustering on articles |
| `/api/mining/classification` | POST | Train/Evaluate category classifier |
| `/api/debug` | GET | Full pipeline explanation |
| `/api/categories` | GET | List all categories |
| `/api/sources` | GET | List all sources |
| `/api/stats` | GET | Corpus statistics |

| `/api/llm/configure` | POST | Configure LM Studio endpoint |

---

## Project Structure

```
a:\MSC\sem 2\project\code\
├── backend/
│   ├── app.py                 # Flask app & routes
│   ├── ir_engine.py           # TF-IDF & ranking
│   ├── analytics_engine.py    # Basic analytics
│   ├── mining_engine.py       # [NEW] Advanced mining (Clustering, Association)
│   ├── database.py            # DuckDB operations

│   ├── preprocessor.py        # Text preprocessing
│   ├── llm_service.py         # LM Studio/Ollama integration
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── styles.css
│   ├── app.js
│   ├── ir-mode.js
│   └── analytics-mode.js
└── data/
    ├── news_articles.csv      # Your dataset
    └── news_corpus.duckdb     # Generated DB file
```

---

## LLM Configuration

**LM Studio** (OpenAI-compatible API):
- Default endpoint: `http://localhost:1234/v1/chat/completions`
- Enable "Developer Mode" in LM Studio settings
- Auto-detected when server is running

**Fallback**: Rule-based explanations when no LLM is available.

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.x, Flask |
| Database | DuckDB (embedded) |
| IR Engine | scikit-learn TF-IDF |
| Frontend | HTML5, CSS3, JavaScript |
| Charts | Chart.js |
| LLM | LM Studio (or Ollama) |

---

## Quick Start

1. Download dataset → save as `data/news_articles.csv`
2. `pip install -r requirements.txt`
3. Start LM Studio → Enable Developer Mode
4. `python app.py`
5. Open `frontend/index.html` in browser
