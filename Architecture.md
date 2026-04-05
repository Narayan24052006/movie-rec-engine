# ARCHITECTURE.md: Advanced Hybrid Movie Recommendation Engine

## 1. Project Overview
**Objective:** Build a production-grade hybrid recommender system combining content-based features and collaborative filtering, featuring proper cold-start handling and an online-style re-ranking mechanism. 
**Primary Persona:** The end-user logging into a Streamlit UI to receive Top-N recommendations, similar items, and explanations for *why* items were recommended.

## 2. Technology Stack
* **Language:** Python 3.10+
* **Data Processing:** `pandas`, `numpy`
* **Machine Learning (Content):** `scikit-learn` (TF-IDF, Cosine Similarity)
* **Machine Learning (Collaborative):** `Surprise`, `implicit`, or `LightFM`
* **Backend / API:** `FastAPI`, `uvicorn`
* **Frontend / UI:** `Streamlit`
* **Data Source:** MovieLens 1M (ratings.csv, movies.csv, tags.csv)

## 3. System Components & Pipeline Tasks

### Phase 1: Data Preparation & Feature Engineering
* **Merge Strategy:** Combine ratings with movie metadata (genres, tags, overview text).
* **Splitting Strategy:** Implement **user-stratified** train/validation/test splits. Do not use simple random splits to avoid data leakage and ensure every user has historical data in the training set.

### Phase 2: Content-Based Model (CBF)
* **Features:** Extract text features from overviews/tags using TF-IDF. Apply one-hot encoding to genres.
* **Similarity:** Compute cosine similarity matrices for item-item recommendations.

### Phase 3: Collaborative Filtering Model (CF)
* **Implementation:** Build at least one of the following: Matrix Factorization (SVD/ALS) OR Neural Collaborative Filtering.
* **Optimization:** Utilize Grid Search or Bayesian Optimization to tune hyperparameters.

### Phase 4: Hybridization & Re-Ranking
* **Strategy:** Implement either a weighted score blend (CF + CBF) OR model stacking (using a Learning-to-Rank approach).
* **Ranking Features:** Final rank must consider CF score, Content score, item popularity, and recency.

### Phase 5: Cold-Start Handling
* **New Users (User Cold-Start):** Design a mechanism for a short UI "quiz" to seed initial preferences.
* **New Items (Item Cold-Start):** Implement a pure content-only fallback for items with zero historical interactions.

### Phase 6: Serving Layer & UI
* **API:** FastAPI endpoints for `/recommendations/{user_id}`, `/similar-items/{item_id}`, and `/explain/{user_id}/{item_id}`.
* **UI:** Streamlit dashboard allowing login as test users to view Top-N lists and read the "Why recommended" (key features/tags) explanations.

## 4. Evaluation Strategy
Offline metrics must be calculated and presented in a Jupyter Notebook (`evaluation.ipynb`). 
Compare the standalone Content model, the standalone CF model, and the Final Hybrid model using:
* Precision@k
* Recall@k
* nDCG@k
* Mean Average Precision (MAP)

## 5. Grading Rubric (100 Points Total)
***AGENT DIRECTIVE: Prioritize code generation and architectural decisions based on these weights.***
* [15 pts] Data/Features (Merging, stratified splitting)
* [20 pts] CF model (Implementation and tuning)
* [15 pts] Content model (TF-IDF, Cosine Sim)
* [20 pts] Hybrid/Ranking (Blending/Stacking logic)
* [10 pts] Cold-start (New user quiz, new item fallback)
* [15 pts] Evaluation (Metric tables, plots, model comparison)
* [05 pts] Serving/UI (FastAPI + Streamlit demo)

## 6. Bonus Objectives (+10 Points)
* **Stretch Goal:** Implement diversity/novelty re-ranking OR session-aware recommendations (using LSTM/Transformer architectures).