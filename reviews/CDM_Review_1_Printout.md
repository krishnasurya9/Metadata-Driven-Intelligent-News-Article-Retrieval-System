# Concepts of Data Mining (CDM) - Review 1
**Project:** Automated Data Mining and Pattern Discovery System for Unstructured News Corpora
## 1. Download Dataset from the Site (Dataset)
The primary dataset involves ingesting structured CSV repositories (such as "All the News" or "AG News") and translating them into an offline warehouse (`news_corpus.duckdb`). This ensures that rigorous Data Mining strategies can be applied to thousands of localized, static records.
**Raw Data Sample (Uncleaned):**
This represents the data exactly as it was downloaded from the site before any algorithmic execution. It contains punctuation, stop-words, and inconsistent casing.
**Document 0:**
> "Celebrity chef Anthony Bourdain, who passed away in June this year, has been honoured with six awards posthumously at this year's Creative Arts Emmys for his CNN show 'Anthony Bourdain: Parts Unknown' and its digital spin-off. His TV series won in five out of six categories in which it was nominated. Bourdain won Outstanding Writing For A Nonfiction Program award."
**Document 1:**
> "World's most valuable bank JPMorgan Chase's CEO Jamie Dimon said, the US 'is truly an exceptional country' and 'it is clear that something is wrong'. In a 45-page letter to shareholders, Dimon wrote US has dumped trillions of dollars into wars and piled huge debt onto students. Further, US has forced foreigners to leave after getting advanced degrees, he added."
## 2. Feature Selection for the Project (Features / Attributes)
Relevant independent variables and metrics are extracted from the raw data to drive analytical discovery. 
*   **Semantic Text Features:** The core textual strings (Full Text, Titles) are vectorized to establish frequencies of distinct term attributes. Top features include recognized entities and thematic nouns (e.g., *bourdain*, *jpmorgan*, *bank*, *emmys*).
*   **Temporal Features (Date/Time):** Extracted publication dates act as the primary feature for time-series trend charting.
*   **Categorical Features (Source Authority/Tags):** Features representing the publisher and specific news categories are selected as core clustering attributes to measure dataset bias and variety.
## 3. Data Preprocessing and Cleaning (Cleaned Data)
Raw dataset strings are subjected to a rigorous data integration and cleaning pipeline prior to loading into analytical models. Syntactical noise (caps, commas, special characters) is entirely stripped, and mathematically irrelevant stop-words are removed.
**Cleaned Data Sample (Algorithmic Output):**
This demonstrates the mathematical translation of the raw data from Section 1 into pure semantic features ready for modeling. Note the complete removal of punctuation and reduction to lowercase base tokens.
| Document # | Cleaned Semantic Features |
| :--- | :--- |
| **Doc 0** | "celebrity chef anthony bourdain who passed away in june this year has been honoured with six awards posthumously at this year s creative arts emmys for his cnn show anthony bourdain parts unknown and its digital spin off his tv series won in five out of six categories in which it was nominated bourdain won outstanding writing for a nonfiction program award" |
| **Doc 1** | "world s most valuable bank jpmorgan chase s ceo jamie dimon said the us is truly an exceptional country and it is clear that something is wrong in a 45 page letter to shareholders dimon wrote us has dumped trillions of dollars into wars and piled huge debt onto students further us has forced foreigners to leave after getting advanced degrees he added" |
Relevant independent variables and metrics are extracted from the raw data to drive analytical discovery. 
*   **Semantic Text Features:** The core textual strings (Full Text, Titles) are vectorized to establish frequencies of distinct term attributes. Top features include recognized entities and thematic nouns (e.g., *bourdain*, *jpmorgan*, *bank*, *emmys*).
*   **Temporal Features (Date/Time):** Extracted publication dates act as the primary feature for time-series trend charting.
*   **Categorical Features (Source Authority/Tags):** Features representing the publisher and specific news categories are selected as core clustering attributes to measure dataset bias and variety.
## 3. Data Preprocessing and Cleaning (Cleaned Data)
Raw dataset strings are subjected to a rigorous data integration and cleaning pipeline prior to loading into analytical models.
*   **Integration:** Heterogeneous date and string formatting from disparate sources are merged into a unified schema format.
*   **Transformation (Lowercasing & Punctuation Removal):** Syntactical noise (caps, commas, special characters) is entirely stripped from the records to ensure consistency.
*   **Cleaning (Stop-Word Elimination):** High-frequency, mathematically irrelevant words (e.g., *the, is, at, which, on*) are eliminated from the dataset structure so that only meaningful semantic features drop into the core models.
**Cleaned Data Sample (Algorithmic Output):**
This demonstrates the mathematical translation of the raw data from Section 1 into pure semantic features ready for modeling. Note the complete removal of punctuation and reduction to lowercase base tokens.
**Document 0 (Cleaned):**
> celebrity chef anthony bourdain who passed away in june this year has been honoured with six awards posthumously at this year s creative arts emmys for his cnn show anthony bourdain parts unknown and its digital spin off his tv series won in five out of six categories in which it was nominated bourdain won outstanding writing for a nonfiction program award
**Document 1 (Cleaned):**
> world s most valuable bank jpmorgan chase s ceo jamie dimon said the us is truly an exceptional country and it is clear that something is wrong in a 45 page letter to shareholders dimon wrote us has dumped trillions of dollars into wars and piled huge debt onto students further us has forced foreigners to leave after getting advanced degrees he added
## 4. Identify Dashboard Requirements based on Data Correlation
The graphical output of the Data Mining models dictates the following dashboard requirements:
*   **Data Correlation Stratification:** The dashboard must be able to visually contrast metrics found in the "Top 20" associated documents versus the "Bottom 20" documents.
*   **Categorical Breakdown Requirement:** Pie or segment charts specifically demonstrating the distribution of categorical features (e.g., Business vs. Technology news distributions).
*   **Temporal Trend Charts:** A line chart mapping the occurrence frequency of extracted attributes over time.
## 5. Project Schedule (Roadmap)
### Phase 1: Project Approval Mechanism (Cut-Off: 20-02-2026)
*   **Step 1:** Project enquiry / investigation. Identify potential projects in a domain (Due: 15-02-2026) -> *Nil*
*   **Step 2:** Finalize 2 to 3 concepts (Due: 20-02-2026) -> *List of titles and 500-word abstracts*
*   **Step 3:** Get consent from staff (Due: 20-02-2026) -> *Approved proposal*
### Phase 2: Project Analysis (**REVIEW 1 Cut-Off: 12-03-2026**)
*   **Step 1:** Download dataset from the site -> *Dataset*
*   **Step 2:** Feature selection for the project -> *Features / Attributes*
*   **Step 3:** Data preprocessing and cleaning, integration, transformation etc. -> *Cleaned data*
*   **Step 4:** Identify dashboard requirements based on data correlation -> *Dashboard requirements*
*   **Step 5:** Project Schedule -> *Gantt Chart*
*   **Step 6:** Presentation (Due: 12-03-2026) -> *Powerpoint presentation*

### Phase 3: System Design (**REVIEW 2 Cut-Off: 25-03-2026**)
*   **Step 1:** Data Analytics -> *Respective design document*
*   **Step 2:** High level system architecture design -> *Respective design document*
*   **Step 3:** Database / Warehouse design -> *Respective design document*
*   **Step 4:** Screen / Input / Form design -> *Respective design document*
*   **Step 5:** Visualization / Graph / Chart design -> *Respective design document*
*   **Step 6:** Test data and test case design -> *Respective design document*

### Phase 4: Coding & Testing (**REVIEW 3 Cut-Off: 10-04-2026**)
*   **Step 1:** ML algorithm implementation on the data -> *Screens/Forms*
*   **Step 2:** User interface development
*   **Step 3:** System integration
*   **Step 4:** Unit/functional/system testing -> *Bug free system*

### Phase 5: Deliverables
*   **Analytics Dashboard Ready (PROTOTYPE):** Functional System Ready (Cut-Off: 15-04-2026)
*   **Documentation (REPORT):** Record Book (Project Cut-Off: 25-04-2026)


