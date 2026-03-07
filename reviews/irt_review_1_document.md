# Information Retrieval Techniques (IRT)
**Review 1: Proposal Review Document**

> **Note:** This document is formulated explicitly to address the components of the IRT Review 1 syllabus: Problem Identification, Objectives & Scope, Literature Review, Dataset Identification, Proposed Methodology, and Presentation Guidelines.

## 1. Problem Identification
**Project Title:** Metadata-Driven Intelligent News Article Retrieval System
**Problem Statement:** The exponential growth of digital news creates massive daily article volumes across diverse domains. Traditional Information Retrieval (IR) systems face critical challenges in these environments:
*   **Context Failure:** Inability to capture deep contextual relevance beyond basic keyword overlap.
*   **Metadata Blindness:** Rich, latent signals (such as source authority, publication dates, and embedded tags) are frequently ignored in favor of simple lexical matching.
*   **Lack of Synthesis:** End-users are bombarded with raw lists of links rather than coherent, synthesized answers natively explaining the knowledge.

**Real-World Relevance:** Overcoming these obstacles is critical for effective media monitoring, precise sentiment tracking, and academic research. A localized, explainable system empowers researchers to sift through noise safely, offline, and accurately.

## 2. Objectives & Scope
**Objectives:**
*   **Primary Goal:** To fundamentally develop a standalone, explainable AI system specifically optimized for news intelligence and retrieval.
*   Overcome "Metadata Blindness" by integrating date, source, and tag weighting directly into the ranking mechanics, moving significantly beyond standard text matching.
*   Establish an "Offline First" architecture utilizing an embedded DuckDB structure, guaranteeing reproducibility without external cloud dependencies.
*   Design a transparent Information Retrieval pipeline prioritizing Explainable AI (XAI), explicitly demonstrating to the user *why* specific documents are retrieved and ranked.

**Scope & Limitations:**
*   **Scope:** Focuses exclusively on textual data retrieval utilizing hybrid scoring (combining text similarity with metadata weights). The framework focuses primarily on classifying the "Top 20" vs "Bottom 20" retrieval sets. 
*   **Limitations:** The small-scale Large Language Models (LLMs) via Ollama/LM Studio deployed post-retrieval act *strictly* as synthesizers grounding their factual answers only in retrieved documents; they are intentionally disconnected from open-ended web generation to maintain strict contextual boundaries.

## 3. Literature Review (Background & Concepts)
> **Rubric Requirement:** Minimum 5-8 papers demonstrating relevance and understanding.

The system's architecture is built upon the foundational concepts established in the following key academic domains (papers to be added):
1.  **[Placeholder: Paper 1 on TF-IDF Optimization]** - Validation of the core 'Base Scoring' mechanism used in our pipeline.
2.  **[Placeholder: Paper 2 on Probabilistic IR (BM25)]** - Justification for evaluating document relevancy dynamically based on term saturation.
3.  **[Placeholder: Paper 3 on Dense Neural Embeddings]** - Required for understanding the limitations of sparse retrieval vs. our planned hybrid semantic approach.
4.  **[Placeholder: Paper 4 on Retrieval-Augmented Generation (RAG)]** - Serves as the blueprint for why our local LLMs act *exclusively* as post-retrieval synthesizers rather than search engines.
5.  **[Placeholder: Paper 5 on Offline Database Architecture]** - Provides the academic baseline for transitioning away from heavy cloud databases to localized analytical querying for rapid IR processing.
6.  **[Placeholder: Paper 6 on Metadata Contextualization]** - Validating Recency/Source Authority weighting in news domains.

**Key Concepts Explored From Literature:**
*   **Sparse vs. Dense Retrieval:** Analysis of traditional term-frequency algorithms versus dense neural embeddings (`sentence-transformers`), noting that hybrid approaches yield the best context preservation.
*   **Embedded Databases in IR:** The shift from heavy SQL servers to embedded analytical databases allows for faster, localized text querying and metric manipulation.
*   **Explainable IR:** Ensuring the opaque nature of search ranking is made transparent to the user by detailing why a document was ranked (e.g., citing the impact of the metadata multiplier against the base score).

## 4. Dataset Identification
**Dataset Strategy:** To support offline, rapid analytical queries without risking API latency, the methodology focuses on robust, static datasets.
*   **Corpora:** High-quality local repositories (like Kaggle's 'All the News', or AG News datasets).
*   **Attributes (Features Required):** Must inherently contain: Full text content, Titles, Summaries, and critical Metadata (Tags, Dates of Publication, Author/Source references).
*   **Justification:** These datasets are essential as they facilitate the rigorous testing of both fundamental tokenization engines and the downstream Recency/Source Authority boosting algorithms.

## 5. Proposed Methodology
**High-Level IR Pipeline Overview:**
1.  **Ingestion:** Import raw documents (full text, titles, summaries).
2.  **Enrichment & Preprocessing:** Automatic extraction of metadata parameters alongside standard text normalization and tokenization. 
3.  **Base Scoring Module:** Core textual matching utilizing established TF-IDF vectors alongside Cosine Similarity matching against user queries.
4.  **Metadata Boosting Module:** Applying multiplicative weights over the base scores (e.g., implementing Recency Multipliers and Source Authority adjustments).
5.  **Retrieval & Organization:** Emphasizing the isolation of Top 20 relevant items, allowing a grounded synthesizer (local LLM) to explain the output contextually and exclusively from that set.
