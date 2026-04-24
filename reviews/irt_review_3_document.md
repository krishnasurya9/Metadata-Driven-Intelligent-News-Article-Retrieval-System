# IRT Review 3 Document: System Development
**Information Retrieval Techniques**

## 1. Final Integrated System
- Offline-first Flask backend + DuckDB storage + hybrid IR engine.
- Retrieval combines BM25 and FAISS semantic vectors with metadata-aware scoring.
- Frontend supports search, status checks, and explainable summary output.

## 2. Implemented Pipeline
1. Ingestion to warehouse
2. Index build/load (BM25 + FAISS)
3. Query processing
4. Hybrid ranking and metrics
5. Result rendering + optional LLM summary

## 3. Evaluation Snapshot
- Scripted evaluation and API tests are available.
- Core runtime metrics captured:
  - Precision
  - Recall
  - F1
  - MAP (approx)

## 4. Engineering Improvements
- Incremental index updates for new documents.
- Index status monitoring endpoints.
- Better API contract stability between frontend and backend.

## 5. Limitations
- Evaluation still needs larger human-judged relevance sets for publication-level rigor.
- Heavy embedding operations remain hardware-sensitive.

## 6. Review 3 Conclusion
IRT module is integrated, testable, and demo-ready with hybrid retrieval and clear API flow.
