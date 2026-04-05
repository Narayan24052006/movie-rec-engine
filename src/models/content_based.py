"""
Content-Based Filtering Model
==============================
Uses TF-IDF on combined text features (genres + tags) and cosine
similarity for item-item recommendations.  Genre one-hot encoding is
also available for feature stacking.
"""

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MultiLabelBinarizer

logger = logging.getLogger(__name__)


class ContentBasedModel:
    """Item-item content-based recommender.

    Builds a TF-IDF matrix from movie text features and computes
    cosine similarity for fast item-item lookups.
    """

    def __init__(
        self,
        max_features: int = 10_000,
        ngram_range: Tuple[int, int] = (1, 2),
    ):
        self.max_features = max_features
        self.ngram_range = ngram_range

        # Fitted objects
        self._tfidf: Optional[TfidfVectorizer] = None
        self._tfidf_matrix: Optional[sparse.csr_matrix] = None
        self._genre_matrix: Optional[np.ndarray] = None
        self._combined_matrix: Optional[sparse.csr_matrix] = None
        self._movie_ids: Optional[np.ndarray] = None
        self._movieid_to_idx: Dict[int, int] = {}
        self._mlb: Optional[MultiLabelBinarizer] = None
        self._feature_names: Optional[List[str]] = None

    # ------------------------------------------------------------------
    # Fitting
    # ------------------------------------------------------------------

    def fit(self, movies: pd.DataFrame) -> "ContentBasedModel":
        """Fit on ``movies`` DataFrame.  Expects columns:
        ``movieId``, ``genres`` (pipe-separated), ``combined_text``.
        """
        movies = movies.copy().reset_index(drop=True)
        self._movie_ids = movies["movieId"].values.astype(np.int32)
        self._movieid_to_idx = {
            int(mid): idx for idx, mid in enumerate(self._movie_ids)
        }

        # --- TF-IDF on combined text ---
        self._tfidf = TfidfVectorizer(
            max_features=self.max_features,
            ngram_range=self.ngram_range,
            stop_words="english",
            dtype=np.float32,
        )
        self._tfidf_matrix = self._tfidf.fit_transform(
            movies["combined_text"].fillna("")
        )
        self._feature_names = self._tfidf.get_feature_names_out().tolist()

        # --- Genre one-hot ---
        genre_lists = movies["genres"].fillna("").str.split("|")
        self._mlb = MultiLabelBinarizer()
        self._genre_matrix = self._mlb.fit_transform(genre_lists).astype(np.float32)

        # --- Combined sparse matrix (TF-IDF + genres) ---
        genre_sparse = sparse.csr_matrix(self._genre_matrix)
        self._combined_matrix = sparse.hstack(
            [self._tfidf_matrix, genre_sparse], format="csr"
        )

        logger.info(
            "CBF fitted: %d items, TF-IDF features=%d, genre features=%d",
            len(movies),
            self._tfidf_matrix.shape[1],
            self._genre_matrix.shape[1],
        )
        return self

    # ------------------------------------------------------------------
    # Similarity queries
    # ------------------------------------------------------------------

    def similar_items(
        self, movie_id: int, top_n: int = 20, exclude_self: bool = True
    ) -> List[Tuple[int, float]]:
        """Return the top-N most similar items to ``movie_id``.

        Returns:
            List of (movieId, similarity_score) tuples, descending.
        """
        if movie_id not in self._movieid_to_idx:
            logger.warning("movie_id %d not found in CBF index", movie_id)
            return []

        idx = self._movieid_to_idx[movie_id]
        query_vec = self._combined_matrix[idx]
        scores = cosine_similarity(query_vec, self._combined_matrix).flatten()

        if exclude_self:
            scores[idx] = -1.0

        top_indices = np.argsort(scores)[::-1][:top_n]
        results = [
            (int(self._movie_ids[i]), float(scores[i])) for i in top_indices
        ]
        return results

    def get_content_scores_for_user(
        self,
        liked_movie_ids: List[int],
        all_movie_ids: Optional[List[int]] = None,
        top_n: int = 100,
    ) -> List[Tuple[int, float]]:
        """Compute a user-profile-based content score.

        Builds a centroid vector from the user's liked items and
        returns the most similar items from the full catalogue.
        """
        known_indices = [
            self._movieid_to_idx[mid]
            for mid in liked_movie_ids
            if mid in self._movieid_to_idx
        ]
        if not known_indices:
            return []

        # Average (centroid) profile
        profile = self._combined_matrix[known_indices].mean(axis=0)
        profile = np.asarray(profile)

        scores = cosine_similarity(profile, self._combined_matrix).flatten()

        # Zero-out already-liked items
        for idx in known_indices:
            scores[idx] = -1.0

        if all_movie_ids is not None:
            candidate_indices = [
                self._movieid_to_idx[mid]
                for mid in all_movie_ids
                if mid in self._movieid_to_idx
            ]
            mask = np.full(scores.shape, -1.0)
            for ci in candidate_indices:
                mask[ci] = scores[ci]
            scores = mask

        top_indices = np.argsort(scores)[::-1][:top_n]
        return [
            (int(self._movie_ids[i]), float(scores[i]))
            for i in top_indices
            if scores[i] > 0
        ]

    # ------------------------------------------------------------------
    # Explanation helpers
    # ------------------------------------------------------------------

    def explain_similarity(
        self, movie_id_a: int, movie_id_b: int, top_features: int = 10
    ) -> Dict[str, float]:
        """Return the top contributing TF-IDF features for the similarity
        between two movies (useful for the ``/explain`` endpoint).
        """
        if (
            movie_id_a not in self._movieid_to_idx
            or movie_id_b not in self._movieid_to_idx
        ):
            return {}
        idx_a = self._movieid_to_idx[movie_id_a]
        idx_b = self._movieid_to_idx[movie_id_b]

        vec_a = np.asarray(self._tfidf_matrix[idx_a].todense()).flatten()
        vec_b = np.asarray(self._tfidf_matrix[idx_b].todense()).flatten()

        # Element-wise product shows feature overlap
        product = vec_a * vec_b
        top_idx = np.argsort(product)[::-1][:top_features]

        explanation = {}
        for fi in top_idx:
            if product[fi] <= 0:
                break
            explanation[self._feature_names[fi]] = float(product[fi])
        return explanation

    def get_movie_genres(self, movie_id: int) -> List[str]:
        """Return the genre list for a movie."""
        if movie_id not in self._movieid_to_idx:
            return []
        idx = self._movieid_to_idx[movie_id]
        genre_vec = self._genre_matrix[idx]
        active = np.where(genre_vec > 0)[0]
        return [self._mlb.classes_[i] for i in active]
