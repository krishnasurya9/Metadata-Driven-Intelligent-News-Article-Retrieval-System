# Final Project Documentation: Information Retrieval Techniques (IRT)

**Project Title:** Metadata-Driven Intelligent News Article Retrieval System  
**Module:** Information Retrieval Techniques (IRT)

---

## 1. Project Overview & Objectives
**Goal:** To engineer a standalone, offline capable search engine combining Lexical and Semantic retrieval strategies to parse 120,000+ digital news articles efficiently. 
Given the explosive growth of online journalism, this project transitions away from rudimentary keyword search engines, introducing dense semantic vectors, custom evaluation metrics, and Local LLM (Large Language Model) augmented search explainability.

---

## 2. Project Timeline (IRT Phase)
| Week | Phase | Description of Work Completed |
| :--- | :--- | :--- |
| **Week 1-2** | Ingestion & Schema | Built `news_fetcher.py`. Designed the embedded `DuckDB` warehousing schema. Acquired ~120k articles. |
| **Week 3** | Lexical Indexing | Implemented TF-IDF and BM25 indexing algorithms (`ir_engine.py`). Tested basic lexical lookups. |
| **Week 4** | Semantic Vectors | Implemented `sentence-transformers` (`all-MiniLM-L6-v2`) and embedded `FAISS` high-speed indexing (`vector_engine.py`). |
| **Week 5** | Hybrid Fusion | Merged Lexical and Semantic results using Reciprocal Rank Fusion (RRF) with temporal decay boosting. |
| **Week 6** | Framework API | Wrapped retrieval logic in `Flask` REST APIs. Built basic metrics capturing logic (Precision/Recall calculations). |
| **Week 7** | Frontend Architecture | Built the IR mode UI using Vanilla JS and a modern Tavily-inspired aesthetic. Linked API to search bar. |
| **Week 8** | Generative AI Addition | Implemented Local LLM bridge via `LM Studio`. Summarization APIs built to summarize the top 5 ranking outputs contextually. |
| **Week 9** | Evaluation & Tuning | Generated synthetic ground-truths. Plotted comparative Precision-Recall curves. Fine-tuned the system. |

---

## 3. System Architecture & Components (IRT)

### 3.1 Data Flow Pipeline
1. **Raw Text Ingestion:** Offline `.csv` and live REST endpoints funnel into the `DuckDB` local serverless warehouse. Text is fed to `preprocessor.py` (NLTK lowercasing, stopword dropping).
2. **Dual-Index Generation:** 
   - *Sparse Index:* Pickled BM25 structural index maps term frequencies and exact phrase bounds.
   - *Dense Index:* Pickled FAISS binary indices map vectors capturing conceptual tone.
3. **Hybrid Search Retrieval:** Both algorithms pull candidate lists which are normalized and ranked dynamically via formula fusion.

### 3.2 The User Interface (frontend)
Built dynamically to provide a lightning-fast 'Search Engine' experience. Real-time metrics sidebars evaluate user click-through structures, displaying Precision@20, Average Relevancy, and Search Latency within milliseconds on large datasets.

---

## 4. Challenges Faced & Resolutions (IRT)

### Issue 1: Severe System Freezing & RAM Usage on FAISS Index Generation
* **The Problem:** The `sentence-transformers` embeddings mapped over 120,000 articles instantly saturated System RAM, causing complete crashes of the Flask server during bulk ingestion.
* **The Resolution:** We decoupled index regeneration logic from the main application. It was isolated into an offline background script (`rebuild_index.py`), which builds `.faiss` and `.pkl` binaries offline that the main API server gently loads into static read-only memory.

### Issue 2: Poor Ranking of Ambiguous Concepts
* **The Problem:** A query like `technology AI` would bring up articles simply mentioning the word "technology" 100 times before it brought up nuanced articles discussing explicit AI infrastructure concepts.
* **The Resolution:** Instead of relying strictly on TF-IDF or isolated Dense Vectors, we implemented true Hybrid Fusion. Lexical BM25 ensures the target words exist, while Dense FAISS ensures the context aligns. We mathematically forced a 50/50 blend in the standard model.

### Issue 3: Local LLM Timeout & Context Window Truncation
* **The Problem:** Attempting to summarize 10 retrieved articles using a standard local Mistral/Llama model instantly broke context token limits, completely halting server execution.
* **The Resolution:** Truncated AI input context to strictly the top 5 `content_excerpt` fragments maximum. Implemented rigorous thread timeout boundaries so AI summary generation failure doesn't prevent standard article population on the UI.

---

## 5. Evaluation Metrics & Synthetically Backed Findings
We established mathematical ground truths by auto-generating targeted files (`generate_synthetic_data.py`). 

* **Lexical Validation (BM25):** Showed exceptional Recall but struggled mildly with Semantic Precision.
* **Vector Execution (FAISS):** Exhibited incredibly high contextual Precision (0.80+) on nuanced concept queries. 
* **Final Product Metrics:** By unifying them, our resulting Mean Average Precision (MAP) is dramatically stronger than out-of-the-box text searches across unstructured digital journalism datasets.

---

## 6. Conclusion and Future Scope
We successfully bridged modern enterprise Information Retrieval concepts with localized, embedded, consumer hardware. Moving beyond Google-style primitive scraping, the system fully analyzes semantic density internally without relying on the cloud.

**Future Scope:** 
We envision moving the `FAISS` build generation to an active background synchronization pool (`Redis`/`Celery`) so the index rebuilds cumulatively on the fly when new news enters the database, rather than requiring batched offline reconstruction routines.
