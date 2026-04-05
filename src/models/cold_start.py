"""
Cold-Start Handling Module
===========================
Provides mechanisms for:
  1. New User Cold-Start — UI quiz processing to seed initial preferences
  2. New Item Cold-Start — Content-only fallback for items with no interactions
"""

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np

from src.models.content_based import ContentBasedModel

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Available genres for the quiz
# ---------------------------------------------------------------------------

AVAILABLE_GENRES = [
    "Action", "Adventure", "Animation", "Children's", "Comedy",
    "Crime", "Documentary", "Drama", "Fantasy", "Film-Noir",
    "Horror", "Musical", "Mystery", "Romance", "Sci-Fi",
    "Thriller", "War", "Western",
]


class ColdStartHandler:
    """Handles cold-start scenarios for both users and items."""

    def __init__(
        self,
        cbf_model: ContentBasedModel,
        movies_df: "pd.DataFrame",
        popularity: Optional[Dict[int, float]] = None,
    ):
        self.cbf_model = cbf_model
        self.movies_df = movies_df
        self._popularity = popularity or {}

    # ------------------------------------------------------------------
    # New User — Quiz-based bootstrapping
    # ------------------------------------------------------------------

    def process_user_quiz(
        self,
        preferred_genres: List[str],
        min_rating: float = 3.5,
        top_n: int = 20,
    ) -> List[Dict]:
        """Process a new user's genre quiz and return initial recommendations.

        Strategy:
        1. Find movies matching the preferred genres.
        2. Rank by popularity among those genre-matched movies.
        3. Apply content-based similarity scoring to diversify results.

        Args:
            preferred_genres: List of genre strings from the quiz
                              (e.g. ["Sci-Fi", "Thriller"])
            min_rating: Minimum average rating filter (if available)
            top_n: Number of recommendations to return

        Returns:
            List of recommendation dicts
        """
        if not preferred_genres:
            # Ultimate fallback — most popular movies overall
            return self._popular_movies_fallback(top_n)

        # Find movies that match at least one preferred genre
        genre_set = set(g.lower() for g in preferred_genres)
        mask = self.movies_df["genres"].apply(
            lambda g: bool(
                genre_set & set(x.lower() for x in str(g).split("|"))
            )
        )
        matched = self.movies_df[mask].copy()

        if matched.empty:
            return self._popular_movies_fallback(top_n)

        # Score by popularity
        matched["pop_score"] = matched["movieId"].map(
            lambda mid: self._popularity.get(int(mid), 0.0)
        )
        matched = matched.sort_values("pop_score", ascending=False)

        # Take top candidates and use CBF to diversify
        candidate_ids = matched["movieId"].head(top_n * 3).tolist()
        seed_ids = matched["movieId"].head(5).tolist()

        cbf_recs = self.cbf_model.get_content_scores_for_user(
            seed_ids, all_movie_ids=candidate_ids, top_n=top_n
        )

        results = []
        for mid, score in cbf_recs:
            movie_row = self.movies_df[self.movies_df["movieId"] == mid]
            title = movie_row["title"].iloc[0] if len(movie_row) > 0 else "Unknown"
            genres = movie_row["genres"].iloc[0] if len(movie_row) > 0 else ""
            results.append(
                {
                    "movieId": int(mid),
                    "title": title,
                    "genres": genres,
                    "score": round(score, 4),
                    "source": "cold_start_quiz",
                }
            )

        if not results:
            return self._popular_movies_fallback(top_n)

        return results[:top_n]

    # ------------------------------------------------------------------
    # New Item — Content-only fallback
    # ------------------------------------------------------------------

    def recommend_new_item_similar(
        self, movie_id: int, top_n: int = 20
    ) -> List[Dict]:
        """For a new item with zero interactions, use pure content similarity.

        Args:
            movie_id: The movie ID of the new item

        Returns:
            List of similar movie dicts
        """
        similar = self.cbf_model.similar_items(movie_id, top_n=top_n)
        results = []
        for mid, score in similar:
            movie_row = self.movies_df[self.movies_df["movieId"] == mid]
            title = movie_row["title"].iloc[0] if len(movie_row) > 0 else "Unknown"
            genres = movie_row["genres"].iloc[0] if len(movie_row) > 0 else ""
            results.append(
                {
                    "movieId": int(mid),
                    "title": title,
                    "genres": genres,
                    "similarity": round(score, 4),
                    "source": "content_fallback",
                }
            )
        return results

    def is_cold_start_user(self, user_id: int, known_users: set) -> bool:
        """Check if a user is new (not in training data)."""
        return user_id not in known_users

    def is_cold_start_item(self, movie_id: int, known_items: set) -> bool:
        """Check if an item is new (no historical interactions)."""
        return movie_id not in known_items

    # ------------------------------------------------------------------
    # Fallbacks
    # ------------------------------------------------------------------

    def _popular_movies_fallback(self, top_n: int) -> List[Dict]:
        """Return the most popular movies as a last-resort fallback."""
        sorted_items = sorted(
            self._popularity.items(), key=lambda x: x[1], reverse=True
        )[:top_n]

        results = []
        for mid, pop in sorted_items:
            movie_row = self.movies_df[self.movies_df["movieId"] == mid]
            title = movie_row["title"].iloc[0] if len(movie_row) > 0 else "Unknown"
            genres = movie_row["genres"].iloc[0] if len(movie_row) > 0 else ""
            results.append(
                {
                    "movieId": int(mid),
                    "title": title,
                    "genres": genres,
                    "score": float(pop),
                    "source": "popularity_fallback",
                }
            )
        return results
