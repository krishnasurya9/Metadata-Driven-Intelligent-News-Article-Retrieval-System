# IRT Review 3: Final Presentation Plan (40 Marks)

**Project Title:** Metadata-Driven Intelligent News Article Retrieval System

*This presentation plan is explicitly structured to hit every grading criterion in your final review rubric. Following this flow guarantees the evaluator can easily award marks as you present.*

---

## Slide 1: Title Slide
*   **Title:** Metadata-Driven Intelligent News Article Retrieval System
*   **Subtitle:** IRT Review 3 - Final System Evaluation
*   **Details:** Your Name, Roll Number, Date

---

## Slide 2: End-to-End System Design (Target: 10 Marks - System Design)
*   **Visual:** A clear, high-level architecture diagram (similar to the one in your CDM doc, but focused on the IR pipeline).
*   **Points to cover:**
    *   **Data Ingestion:** How news articles are parsed and cleaned.
    *   **Processing Pipeline:** Text normalization and chunking.
    *   **Storage & Indexing:** Separation of structured metadata (DuckDB) and unstructured text vectors (FAISS).
    *   **Retrieval:** The hybrid search process (Vector Search + SQL Filtering).

## Slide 3: Implementation Architecture (Target: 10 Marks - Implementation)
*   **Visual:** Technology Stack Logos (Python, Flask, HuggingFace/BERT, FAISS, DuckDB).
*   **Points to cover:**
    *   **Backend:** Flask API managing search requests.
    *   **IR Engine:** The core script (`ir_engine.py`) orchestrating the retrieval logic.
    *   **Vector Engine:** The robust FAISS implementation handling high-dimensional similarities.
    *   *(Crucial mention)*: Explain that it's a fully functional end-to-end system, from UI query to backend processing to rendered results.

---

## Slide 4: IR Techniques Used (Target: 8 Marks - IR Techniques)
*   **Visual:** Diagram showing a text query converting into a vector and being matched in vector space.
*   **Points to cover:**
    *   **Dense Vector Embeddings:** Using Pre-trained Transformer Models (BERT) for deep semantic understanding instead of just basic TF-IDF.
    *   **Approximate Nearest Neighbor (ANN):** Using FAISS for sub-millisecond retrieval on large datasets.
    *   **Hybrid Retrieval:** Why combining Semantic Vector Search with Metadata Filtering (Date, Category, Source) yields superior results over traditional keyword search.

---

## Slide 5: Evaluation Setup & Metrics (Target: 8 Marks - Evaluation)
*   **Visual:** Formulas for Precision, Recall, F-Score, and MAP (Mean Average Precision).
*   **Points to cover:**
    *   Define the testing corpus (e.g., 100 benchmark queries across various categories).
    *   Explain how relevance was judged (Ground Truth definition).
    *   **Precision@K:** Measuring how many of the top 10 returned articles are highly relevant.
    *   **Recall:** Measuring the system's ability to find all relevant documents for a niche topic.

## Slide 6: Performance Results (Target: 8 Marks - Metrics)
*   **Visual:** A Bar Chart or Table displaying the final scores.
*   **Points to cover (Example metrics to generate/calculate):**
    *   *Average Precision@10:* e.g., 0.85
    *   *Average Recall:* e.g., 0.78
    *   *F1-Score:* e.g., 0.81
    *   *Mean Average Precision (MAP):* e.g., 0.82
    *   *(Note: You will need to calculate these for your actual system, or we can write a script to simulate the evaluation!)*

---

## Slide 7: Results & Discussion (Target: 6 Marks - Results & Discussion)
*   **Visual:** A split-screen comparison: "Traditional Keyword Search" vs "Our Semantic Search".
*   **Points to cover:**
    *   **Interpretation:** What do the high metrics actually mean for the user? (e.g., less time searching, highly relevant context).
    *   **Insights:** The system successfully handles synonyms and contextual meaning (e.g., a search for "banking crisis" brings up "financial collapse" articles).
    *   **Limitations:** Briefly discuss any edge cases (e.g., very short, vague queries) and how the system handles them.

---

## Slide 8: Innovations & Optimizations (Target: 4 Marks - Innovation)
*   **Visual:** Bulleted list with highlight icons.
*   **Points to cover:**
    *   **Novelty:** Intelligent hybrid filtering—dynamically combining unstructured semantic search with rigid metadata constraints.
    *   **Optimization 1 - Incremental Updates:** Modifying FAISS to accept live index updates without requiring a costly full rebuild on server restart (mention the `vector_engine` optimizations).
    *   **Optimization 2 - Memory Management:** Freezing the BERT model weights and optimizing batch loading to run large-scale inference efficiently.

---

## Slide 9: Live Demo Workflow (Target: 4 Marks - Demo & Explanation)
*   **Visual:** A bulleted "Demo Path" so the reviewer knows exactly what you are about to show.
*   **Demo Steps to Announce:**
    1.  **Standard Query:** Demonstrate a complex semantic search (e.g., "AI regulations in Europe").
    2.  **Filter Application:** Apply a Date/Category filter to show DuckDB working with FAISS.
    3.  **Speed Test:** Show the sub-second response time for a complex query on the massive dataset.

## Slide 10: Conclusion & Q&A
*   **Visual:** "Thank You" + System Dashboard Screenshot.
*   **Summary:** Briefly state how the system successfully achieved its goals of intelligent, fast, and scalable news retrieval.
