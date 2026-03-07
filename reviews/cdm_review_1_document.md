# Concepts of Data Mining (CDM)
**Review 1: Project Analysis Document**

## 1. Project Background (Approval Mechanism)
## 1. Project Background & Approval Mechanism
**Finalized Project Title:** Automated Data Mining and Pattern Discovery System for Unstructured News Corpora
**(Alias:** *Automated Trend Analysis and Sentiment Mining System*)

**Project Abstract (~500 Word Conceptual Overview):**
The exponential growth of digital media has resulted in massive repositories of unstructured text, creating a state of "Digital News Overload." Traditional information retrieval systems are insufficient for modern analytical needs because they suffer from "Context Failure" and "Metadata Blindness"—they effectively retrieve words but fail to discover underlying patterns, semantic relationships, or the temporal dynamics of news events. 

This project addresses this critical gap by developing a standalone, analytical AI system designed specifically to transform raw, unstructured news articles into transparent, structured knowledge. The core proposition of this system is to move beyond simple document retrieval into unsupervised and supervised Data Mining. By ingesting streams of data from high-volume public APIs (The Guardian, NewsAPI) and robust archival CSVs (Kaggle's "All the News," AG News) into a unified, embedded DuckDB warehouse, the system establishes a local "Offline First" foundation for analysis.

The system's methodology executes a rigorous data mining pipeline: raw text undergoes strict preprocessing and tokenization, translating linguistic data into high-dimensional TF-IDF matrices. From this cleansed data, the system extracts critical metadata attributes—such as Source Authority and Publication Dates—which act as independent variables for correlation. Unlike conventional 'black box' search engines, this system autonomously discovers hidden semantic relationships using embedded algorithms. 

To bridge the gap between complex data mining outputs and user interpretation, the system features an "Analytics Mode" dashboard. This dashboard visualizes categorical distributions, tracks term frequencies across temporal bounds, and establishes correlation dichotomies (Top 20 vs. Bottom 20 document stratification). Crucially, the system introduces a layer of Explainable AI (XAI) Synthesis via Retrieval-Augmented Generation (RAG), utilizing localized Small Language Models (Ollama/LM Studio). These models are isolated from the generation of external internet data; instead, they act strictly as analytical interpreters that explain *why* visual patterns and data correlations exist natively within the warehoused corpus.

Ultimately, this project provides a multifaceted tool for automated opinion mining, real-time event tracking, and knowledge discovery, serving as a powerful, explainable architecture for journalism analytics and brand intelligence safely housed on local infrastructure.

**Domain Research:** Addresses the critical need for automated opinion mining, capturing deep contextual relevance, and explainable AI pattern discovery in journalism.

## 2. Project Analysis (Current Progress)

### 2.1 Download Dataset from the Site
**Dataset Deliverables & Sources:**
The system establishes a robust Data Warehouse capable of ingesting diverse text streams without relying on external cloud databases.
*   **Primary Datasets:** Heavy reliance on structured corpora (e.g., Kaggle's "All the News" or "AG News") that inherently contain Full Text, Titles, and Summaries.
*   **Warehousing Engine:** The data is successfully mapped into an embedded DuckDB instance (`news_corpus.duckdb`), which allows for direct no-install analytical querying directly from the local file system.
*   **Deliverable Verification:** Raw textual data is successfully warehoused locally within the system directories.

### 2.2 Feature Selection for the Project
**Features / Attributes Deliverables:**
Raw documents are mapped to specific, mathematically usable attributes to drive the analytical dashboard.
*   **Extracted Features (The Enrichment Phase):** The initial pipeline successfully pulls standard metadata variables: `Tags`, `Dates`, and `Sources`.
*   **Textual Matrix Features:** The core textual strings (Full Text, Titles) are translated into Tokenized models (TF-IDF matrices) prioritizing text similarity scores.
*   **Metadata Bounding:** The key distinction of this project is applying mathematical weights to features (specifically assigning a "Recency Multiplier" to dates and a "Source Authority" metric to publishers).

### 2.3 Data Preprocessing and Cleaning, Integration, Transformation
**Cleaned Data Deliverables:**
Data Preprocessing is handled automatically by the ingestion pipeline before base-scoring.
*   **Integration & ETL:** Heterogeneous datasets are harmonized into the DuckDB unified format.
*   **Cleaning:** The pipeline successfully executes raw text tokenization and rigorous standard text normalization (stripping stop-words/punctuation).
*   **Transformation:** Text metrics are filtered down to base forms creating the "Base Scoring" baseline, ensuring subsequent analytical rules operate on purely semantic concepts rather than syntactic noise.

### 2.4 Identify Dashboard Requirements based on Data Correlation
**Dashboard Requirements Deliverables:**
The visual "Analytics Mode" (served via `analytics-mode.js`) acts as the user's primary interactive mechanism. Based on data correlations mapped locally, the dashboard mandates the following:
*   **Rank Group Separation:** The dashboard must clearly establish a correlation dichotomy, explicitly separating patterns found in the "Top 20" retrieval set versus the "Bottom 20" retrieval set.
*   **Metadata Visualizers:** Charts establishing frequency relationships between extracted metadata tags (e.g., how often Date correlates to a specific Source Authority).
*   **Explainable (XAI) Synthesis Requirement:** Unlike raw text dashboards, a core requirement is the integration of small local LLMs (`llm_service.py` via Ollama/LM Studio). The dashboard must use these models *exclusively* to explain why visual patterns exist based on the dataset (ensuring factual grounding without hallucination).

### 2.5 Project Schedule (Gantt Chart Roadmap)
**Deliverable: Gantt Chart Scheduling (Mapped Constraints)**
To ensure successful deployment, the project is structured across the following scheduling phases:

*   **Phase 1: Project Approval & Analysis (Cut-Off: Feb 20, 2026)**
    *   *Tasks:* Initial project investigation, finalize 500-word abstract, obtain faculty concept approval.
    *   *Status:* **Completed.**
*   **Phase 2: Data Pipeline & Base Architecture (Cut-Off: Mar 12, 2026 - Review 1)**
    *   *Tasks:* Download datasets (AG News/BBC), implement DuckDB warehouse, perform script-based data cleaning/integration (`preprocessor.py`), select TF/IDF features, define dashboard requirements.
    *   *Status:* **Completed.**
*   **Phase 3: System Design & Visualizations (Cut-Off: Mar 25, 2026 - Review 2)**
    *   *Tasks:* High-level architectural wireframes, API endpoint creation (Flask), Analytics Dashboard visual design (Chart.js integrations for term frequencies/categories).
    *   *Status:* **In Progress.**
*   **Phase 4: Advanced Coding & Testing (Cut-Off: Apr 10, 2026 - Review 3)**
    *   *Tasks:* Finalize unsupervised data mining algorithms mapping, integrate local LLM `llm_service.py` for XAI synthesis, execute Unit/Integration testing across the local corpus.
    *   *Status:* **Pending.**
*   **Phase 5: Final Delivery (Cut-Off: Apr 25, 2026)**
    *   *Tasks:* Analytics Dashboard Fully Functional. Submit Record Book and Finalized code repository.
    *   *Status:* **Pending.**
