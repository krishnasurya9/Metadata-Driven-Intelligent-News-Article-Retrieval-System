# IRT Review 2 Document
**Information Retrieval Techniques**

## 1. Model Architecture & Methodology
### 1.1 High-Level Architecture
The Information Retrieval system is built offline-first using Flask, DuckDB, and FAISS. It employs a two-tier retrieval methodology:
- **Lexical Search (BM25):** Fast keyword matching using term frequency algorithms on the pre-built index.
- **Semantic Search (Dense Vector):** Contextual meaning extraction utilizing Sentence-Transformers and a FAISS index.

### 1.2 Weighted Hybrid Ranking Methodology
Upon retrieval, documents from both tiers are normalized and scored using a weighted formula:
`Final Score = (w1 * Vector_Score) + (w2 * Lexical_Score) + (w3 * Author/Recency_Multiplier)`

## 2. Experimental Setup & Data Collection
### 2.1 Dataset
- Source: AG News Corpus and Live News Fetchers.
- Characteristics: ~120,000 multi-class categorized news articles.
### 2.2 Live Data Ingestion
- Background orchestration threads periodically pull from NewsAPI, Guardian API, and Mediastack.
- Data is normalized into a unified schema for storage in the DuckDB spatial warehouse.

## 3. Exploratory Data Analysis (EDA)
- **Class Distribution:** Analysis of document frequency among major categories (World, Sports, Business, Sci/Tech).
- **Term Frequencies:** Extracting top terms to define stop-word adjustments.
- **Length Distribution:** Evaluating the average token count of articles to inform BM25 parameter tuning.

## 4. Preprocessing Pipeline
Text undergoes rigorous structural normalization via NLTK-based `preprocessor.py`:
1. Lowercasing
2. Punctuation & Special Character Removal (Regex)
3. Stopword Filtration
4. Stemming via PorterStemmer
5. Tokenization for Lexical processing

## 5. Feature Extraction
### 5.1 Lexical Features
- **TF-IDF Construction:** Document matrices optimized via `scikit-learn` (`min_df`, `max_features` constraints).
- **BM25 Weights:** Statistical representation mapped per term.

### 5.2 Dense Features
- **Sentence Embeddings:** Converting cleaned text bodies into high-dimensional numerical vectors (384-d using standard `all-MiniLM-L6-v2`) for cosine-similarity evaluation in FAISS.

## 6. Issues Faced & Resolutions
Building an offline-first Information Retrieval system highlighted several domain-specific challenges:

1. **Zero-Score Errors in BM25 Retrievals:**
   - *Issue:* High-specificity queries often resulted in a "Zero Score" from the BM25 algorithm due to harsh lexical restrictions on token overlapping. This inadvertently filtered out documents that held deep semantic relation but lacked exact lexical matches.
   - *Resolution:* Edited the hybrid retrieval fusion. If BM25 scores a document `0.0` but the dense FAISS vector yields a positive similarity, an artificial floor (0.001) is granted to the BM25 dimension to allow the Hybrid math (`alpha + beta + gamma`) to boost the semantic discovery correctly.

2. **Full Corpus Indexing CPU Latency (The "Hour Long Boot" Bug):**
   - *Issue:* Because FAISS vector encoding operates via heavy tensor transformations, the background `news_fetcher` previously caused the backend to freeze for up to an hour because it commanded a full 120,000 document vector rebuild even if only 5 new articles were fetched.
   - *Resolution:* Re-architected `vector_engine.py` and `ir_engine.py` to support *Incremental Indexing*. Text documents are now counted on fetch completion, and only completely new SQL row inputs trigger the `SentenceTransformer` encoders. These rows are then safely appended via the `faiss.IndexFlatIP.add()` function.

3. **Inconsistent UI States During Deep Search Processing:**
   - *Issue:* Users were confused about whether the backend was actively processing 120,000 FAISS candidates or had frozen, as search queries took roughly 1.5 seconds.
   - *Resolution:* Implemented an animated, persistent DOM-level progress loading bar mapped synchronously to JavaScript's `await apiCall()` async bounds.
