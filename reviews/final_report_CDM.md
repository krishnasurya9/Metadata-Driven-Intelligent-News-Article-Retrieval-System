# Final Project Documentation: Concepts of Data Mining (CDM)

**Project Title:** Automated Data Mining and Pattern Discovery System  
**Module:** Concepts of Data Mining (CDM)

---

## 1. Project Overview & Objectives
**Goal:** To engineer a secondary internal analysis lab operating over a frozen news corpus to auto-categorize, cluster, and discover underlying event correlations analytically.
While the Information Retrieval system deals with fulfilling user queries, the CDM engine's main duty is to uncover mathematically correlated subtext without external user prompting. 

---

## 2. Project Timeline (CDM Phase)
| Week | Phase | Description of Work Completed |
| :--- | :--- | :--- |
| **Week 1-2** | Data Preprocessing | Cleaned and isolated a 120k row `frozen_corpus.csv`. Generated unified Pandas structures (`cdm_analytics/preprocessing.py`). |
| **Week 3** | Text Normalization | Vectorized content using heavily compressed top 5,000-feature `TF-IDF` maps. Tested memory safety over massive matrices. |
| **Week 4** | Association Mining | Implemented classical `Apriori` rules. Experienced memory crashing. Sub-optimally bounded parameters as temporary fix. |
| **Week 5** | Classification Models | Developed a multi-category classification pipeline comparing `Multinomial Naive Bayes` versus `Linear SVM`. |
| **Week 6** | Clustering & Outliers | Built `Bisecting K-Means` algorithms on top of `Latent Semantic Analysis` (LSA) matrices to isolate distinct topic themes and discover outliers. |
| **Week 7** | Refactoring Apriori | Ripped out Apriori logic completely due to continuous constraints. Built massive-correlation tables successfully leveraging `FP-Growth` FP-trees logic (`mlxtend`). |
| **Week 8** | Interactive Visual UX | Developed Python-to-JSON visual bridges projecting 100D K-Means spaces onto interactive Chart.js 2D PCA Scatter interfaces on the Frontend UI. |
| **Week 9** | Empirical Testing | Fixed backend HTTP 500 edge cases, ran rigorous silhouette score validations on clustering boundaries, established Final Benchmarks. |

---

## 3. System Architecture & Components (CDM)

### 3.1 Unsupervised Pipeline (Clustering & FP Tracking)
1. **Dimensionality Reduction:** Operating K-Means natively on a 10,000 column TF-IDF matrix is fundamentally flawed (Curse of Dimensionality). We utilized `TruncatedSVD` (LSA) to cut this to exactly 100 mathematical vectors.
2. **Bisecting K-Means isolation:** Utilizing strict binary division, the system groups events together natively and classifies collections mathematically smaller than the mean norm as potential reporting "outliers".
3. **Association Generation:** Replaced Apriori itemsets entirely with the memory-efficient FP-Growth methodology. Calculates raw keyword correlations alongside algorithmic Lift. 

### 3.2 Supervised Pipeline (Classification Benchmark)
Instead of forcing a single classification paradigm, the architecture automatically splits testing sets identically and forces both a probabilistic model (`MultinomialNB`) and a dimensional hyperplane model (`Linear SVC`) to race, actively showcasing which parses journalism context better in real-time.

---

## 4. Challenges Faced & Resolutions (CDM)

### Issue 1: High Variance Causing "No Rules Found" / Apriori Memory Overruns
* **The Problem:** Passing a dictionary of 120,000 articles containing 10,000 variables directly into `Apriori` with a standard support bound crashed the application due to astronomical permutation tracking overhead. Conversely, setting bounds too high resulted in valid analytical edge cases destroying the internal Flask API returning HTTP 500 exceptions since it found 0 results. 
* **The Resolution:** Switched to standard `FP-Growth` methodology (via `mlxtend`), significantly reducing required processing overhead. Also modified the codebase to elegantly interpret mathematically "zero" conditions out of bounds and return clear visualization arrays instead of causing server failure. 

### Issue 2: Scipy CSR Matrix Incompatibility with Pandas Boolean Referencing
* **The Problem:** In our Advanced Keyword parsing pipeline (`/api/cdm/keywords`), using Pandas internal Boolean string arrays to extract matrices natively caused `.nonzero()` index fault crashes against Python sparse arrays inside `scikit-learn`.
* **The Resolution:** Diagnosed memory-space bounds correctly and resolved by appending direct numpy `.values` extraction to natively feed primitive formats back into the vector engine.

### Issue 3: Inability to Visualize High-Dimensionality
* **The Problem:** Users cannot see 10,000 dimensions of TF-IDF vectors representing K-Means clustering.
* **The Resolution:** Utilized Principal Component Analysis (PCA) methodology natively in `mining_engine.py` to project those complex spaces down to X-Y mappings which cleanly interface via json payload to the custom Javascript visual layout.

---

## 5. Evaluation Metrics & Findings
* **Support Vector Machine Dominance:** The Live SVM universally outperformed Multinomial Naive Bayes across raw accuracy metrics on journalistic texts, validating its usage as the offline category predictor.
* **FP-Growth Lift Identification:** Standard support metric thresholding completely skewed relevant rules; by incorporating `Lift > 1.25`, the module was able to mathematically draw connections (e.g. World Events with Technical Market adjustments) autonomously. 

---

## 6. Conclusion and Future Scope
By implementing both supervised benchmarking algorithms and entirely unsupervised clustering isolation methods, the Data Mining module effortlessly converts previously unused data troves into mathematically verifiable business-intelligence visual graphs. 

**Future Scope:** Add deeper time-series anomaly forecasting routines and transition from static offline dataset visualization (`frozen_corpus`) directly onto the live updating backend warehouse metrics logic, dynamically rebuilding charts daily as news events cascade.
