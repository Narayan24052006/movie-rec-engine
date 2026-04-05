"""
Hybrid Recommendation Model
============================
Blends Content-Based and Collaborative Filtering scores using
weighted combination with popularity and recency re-ranking.
Supports both simple weighted blending and model stacking.
"""

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from src.models.content_based import ContentBasedModel
from src.models.collaborative_filtering import CollaborativeFilteringModel

logger = logging.getLogger(__name__)


class HybridRecommender:
    """Hybrid recommender combining CF and CBF with re-ranking.

    Scoring formula (weighted mode):
        final_score = w_cf * norm(cf_score)
                    + w_cbf * norm(cbf_score)
                    + w_pop * norm(popularity)
                    + w_rec * norm(recency)
    """

    def __init__(
        self,
        cf_model: CollaborativeFilteringModel,
        cbf_model: ContentBasedModel,
        w_cf: float = 0.50,
        w_cbf: float = 0.30,
        w_pop: float = 0.10,
        w_rec: float = 0.10,
    ):
        self.cf_model = cf_model
        self.cbf_model = cbf_model
        self.w_cf = w_cf
        self.w_cbf = w_cbf
        self.w_pop = w_pop
        self.w_rec = w_rec

        # Precomputed metadata (set via set_item_metadata)
        self._popularity: Dict[int, float] = {}
        self._recency: Dict[int, float] = {}
        self._avg_rating: Dict[int, float] = {}
        self._all_movie_ids: List[int] = []

    # ------------------------------------------------------------------
    # Metadata injection
    # ------------------------------------------------------------------

    def set_item_metadata(
        self,
        popularity: pd.Series,
        recency: pd.Series,
        avg_rating: pd.Series,
        all_movie_ids: List[int],
    ) -> None:
        """Inject precomputed popularity, recency and average rating data."""
        self._popularity = popularity.to_dict() if len(popularity) else {}
        self._recency = recency.to_dict() if len(recency) else {}
        self._avg_rating = avg_rating.to_dict() if len(avg_rating) else {}
        self._all_movie_ids = all_movie_ids

    # ------------------------------------------------------------------
    # Min-max normalization
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize(scores: Dict[int, float]) -> Dict[int, float]:
        """Min-max normalize a dict of scores to [0, 1]."""
        if not scores:
            return scores
        vals = list(scores.values())
        lo, hi = min(vals), max(vals)
        rng = hi - lo if hi - lo > 1e-9 else 1.0
        return {k: (v - lo) / rng for k, v in scores.items()}

    # ------------------------------------------------------------------
    # Core recommendation
    # ------------------------------------------------------------------

    def recommend(
        self,
        user_id: int,
        top_n: int = 20,
        candidate_pool_size: int = 200,
    ) -> List[Dict]:
        """Generate hybrid recommendations for a user.

        Returns a list of dicts:
          [{"movieId": int, "score": float, "cf_score": float,
            "cbf_score": float, "pop_score": float, "rec_score": float}, ...]
        """
        # --- Step 1: Get CF candidates ---
        cf_recs = self.cf_model.recommend(
            user_id, top_n=candidate_pool_size, filter_already_liked=True
        )
        cf_scores_raw = {mid: score for mid, score in cf_recs}
        candidate_ids = list(cf_scores_raw.keys())

        # If CF returns nothing (cold-start user), fall back to popular items
        if not candidate_ids:
            candidate_ids = self._get_popular_fallback(candidate_pool_size)
            cf_scores_raw = {mid: 0.0 for mid in candidate_ids}

        # --- Step 2: Get CBF scores for user profile ---
        # Find items the user has already interacted with
        liked_items = self._get_user_liked_items(user_id)
        cbf_recs = self.cbf_model.get_content_scores_for_user(
            liked_items, all_movie_ids=candidate_ids, top_n=candidate_pool_size
        )
        cbf_scores_raw = {mid: score for mid, score in cbf_recs}
        # Fill missing with 0
        for mid in candidate_ids:
            cbf_scores_raw.setdefault(mid, 0.0)

        # --- Step 3: Gather popularity & recency ---
        pop_scores_raw = {
            mid: self._popularity.get(mid, 0.0) for mid in candidate_ids
        }
        rec_scores_raw = {
            mid: self._recency.get(mid, 0.0) for mid in candidate_ids
        }

        # --- Step 4: Normalize all ---
        cf_norm = self._normalize(cf_scores_raw)
        cbf_norm = self._normalize(cbf_scores_raw)
        pop_norm = self._normalize(pop_scores_raw)
        rec_norm = self._normalize(rec_scores_raw)

        # --- Step 5: Weighted blend ---
        results = []
        for mid in candidate_ids:
            final = (
                self.w_cf * cf_norm.get(mid, 0.0)
                + self.w_cbf * cbf_norm.get(mid, 0.0)
                + self.w_pop * pop_norm.get(mid, 0.0)
                + self.w_rec * rec_norm.get(mid, 0.0)
            )
            results.append(
                {
                    "movieId": mid,
                    "score": round(final, 6),
                    "cf_score": round(cf_norm.get(mid, 0.0), 6),
                    "cbf_score": round(cbf_norm.get(mid, 0.0), 6),
                    "pop_score": round(pop_norm.get(mid, 0.0), 6),
                    "rec_score": round(rec_norm.get(mid, 0.0), 6),
                }
            )

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_n]

    # ------------------------------------------------------------------
    # Explanation
    # ------------------------------------------------------------------

    def explain(self, user_id: int, movie_id: int) -> Dict:
        """Explain why a movie was recommended to a user.

        Returns a dict with score breakdown and top content features.
        """
        cf_score = self.cf_model.predict_score(user_id, movie_id)
        liked_items = self._get_user_liked_items(user_id)
        cbf_scores = dict(
            self.cbf_model.get_content_scores_for_user(
                liked_items, all_movie_ids=[movie_id], top_n=1
            )
        )
        cbf_score = cbf_scores.get(movie_id, 0.0)

        # Find most similar liked item for deeper explanation
        best_explanation_features = {}
        best_sim = 0.0
        best_match = None
        for liked_id in liked_items[:20]:  # Limit to top 20 for performance
            sims = self.cbf_model.similar_items(liked_id, top_n=50)
            for sim_id, sim_score in sims:
                if sim_id == movie_id and sim_score > best_sim:
                    best_sim = sim_score
                    best_match = liked_id
                    best_explanation_features = (
                        self.cbf_model.explain_similarity(liked_id, movie_id)
                    )

        genres = self.cbf_model.get_movie_genres(movie_id)

        return {
            "user_id": user_id,
            "movie_id": movie_id,
            "cf_score": round(cf_score, 4),
            "cbf_score": round(cbf_score, 4),
            "popularity": self._popularity.get(movie_id, 0),
            "avg_rating": round(self._avg_rating.get(movie_id, 0.0), 2),
            "genres": genres,
            "most_similar_liked_item": best_match,
            "similarity_to_liked": round(best_sim, 4),
            "top_matching_features": best_explanation_features,
            "explanation_text": self._generate_explanation_text(
                cf_score, cbf_score, genres, best_match, best_explanation_features
            ),
        }

    def _generate_explanation_text(
        self,
        cf_score: float,
        cbf_score: float,
        genres: List[str],
        best_match: Optional[int],
        features: Dict[str, float],
    ) -> str:
        """Generate a human-readable explanation string."""
        parts = []
        if cf_score > 0.1:
            parts.append(
                "Users with similar taste also enjoyed this movie."
            )
        if cbf_score > 0.1:
            genre_str = ", ".join(genres[:3]) if genres else "similar themes"
            parts.append(
                f"This movie shares content features ({genre_str}) "
                f"with movies you've liked."
            )
        if features:
            top_feats = list(features.keys())[:5]
            parts.append(
                f"Key matching features: {', '.join(top_feats)}."
            )
        if not parts:
            parts.append("This is a popular movie you haven't seen yet.")
        return " ".join(parts)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_user_liked_items(self, user_id: int) -> List[int]:
        """Get items the user has positively interacted with from the CF matrix."""
        if user_id not in self.cf_model._user2idx:
            return []
        uidx = self.cf_model._user2idx[user_id]
        row = self.cf_model._user_item_matrix[uidx]
        liked_indices = row.nonzero()[1]
        return [
            int(self.cf_model._idx2item[idx]) for idx in liked_indices
        ]

    def _get_popular_fallback(self, n: int) -> List[int]:
        """Return the top-N most popular movie IDs as a fallback."""
        sorted_items = sorted(
            self._popularity.items(), key=lambda x: x[1], reverse=True
        )
        return [mid for mid, _ in sorted_items[:n]]
