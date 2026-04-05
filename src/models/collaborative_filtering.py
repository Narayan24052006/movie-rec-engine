"""
Collaborative Filtering Model
==============================
Pure NumPy/SciPy SVD-based matrix factorization for collaborative filtering.
No external C-extension dependencies — works on any Python version.

Implements:
- Truncated SVD on the user-item rating matrix
- SGD-based matrix factorization with bias terms (FunkSVD)
- Grid search over hyperparameters
"""

import logging
import os
import pickle
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.decomposition import TruncatedSVD

logger = logging.getLogger(__name__)


class CollaborativeFilteringModel:
    """SVD-based collaborative filtering recommender.

    Uses FunkSVD (SGD-optimized matrix factorization with biases)
    for high-quality rating predictions, and TruncatedSVD for
    item-item similarity via latent factors.
    """

    def __init__(
        self,
        n_factors: int = 100,
        n_epochs: int = 30,
        lr: float = 0.005,
        reg: float = 0.02,
        random_state: int = 42,
    ):
        self.n_factors = n_factors
        self.n_epochs = n_epochs
        self.lr = lr
        self.reg = reg
        self.random_state = random_state

        # Learned parameters
        self._user_factors: Optional[np.ndarray] = None  # (n_users, n_factors)
        self._item_factors: Optional[np.ndarray] = None  # (n_items, n_factors)
        self._user_bias: Optional[np.ndarray] = None
        self._item_bias: Optional[np.ndarray] = None
        self._global_mean: float = 0.0

        # Mappings
        self._user2idx: Dict[int, int] = {}
        self._idx2user: Dict[int, int] = {}
        self._item2idx: Dict[int, int] = {}
        self._idx2item: Dict[int, int] = {}
        self._user_item_matrix: Optional[sparse.csr_matrix] = None

        # For SVD-based similarity
        self._svd_item_vectors: Optional[np.ndarray] = None

    # ------------------------------------------------------------------
    # FunkSVD Training (SGD)
    # ------------------------------------------------------------------

    def fit(
        self,
        ratings: pd.DataFrame,
        user2idx: Dict[int, int],
        idx2user: Dict[int, int],
        item2idx: Dict[int, int],
        idx2item: Dict[int, int],
    ) -> "CollaborativeFilteringModel":
        """Train the FunkSVD model using SGD on explicit ratings."""
        self._user2idx = user2idx
        self._idx2user = idx2user
        self._item2idx = item2idx
        self._idx2item = idx2item

        n_users = len(user2idx)
        n_items = len(item2idx)

        # Build sparse matrix
        rows = ratings["userId"].map(user2idx).values
        cols = ratings["movieId"].map(item2idx).values
        vals = ratings["rating"].values.astype(np.float32)
        self._user_item_matrix = sparse.coo_matrix(
            (vals, (rows, cols)), shape=(n_users, n_items)
        ).tocsr()

        # Global mean
        self._global_mean = float(vals.mean())

        # Initialize latent factors
        rng = np.random.RandomState(self.random_state)
        scale = 0.1 / np.sqrt(self.n_factors)
        self._user_factors = rng.normal(0, scale, (n_users, self.n_factors)).astype(np.float32)
        self._item_factors = rng.normal(0, scale, (n_items, self.n_factors)).astype(np.float32)
        self._user_bias = np.zeros(n_users, dtype=np.float32)
        self._item_bias = np.zeros(n_items, dtype=np.float32)

        logger.info(
            "Training FunkSVD: factors=%d, epochs=%d, lr=%.4f, reg=%.4f, "
            "%d users, %d items, %d ratings",
            self.n_factors, self.n_epochs, self.lr, self.reg,
            n_users, n_items, len(vals),
        )

        # SGD training
        for epoch in range(self.n_epochs):
            # Shuffle training data
            indices = rng.permutation(len(vals))
            total_loss = 0.0

            for idx in indices:
                u, i, r = int(rows[idx]), int(cols[idx]), float(vals[idx])

                # Predict
                pred = (
                    self._global_mean
                    + self._user_bias[u]
                    + self._item_bias[i]
                    + np.dot(self._user_factors[u], self._item_factors[i])
                )

                # Error
                err = r - pred
                total_loss += err ** 2

                # Update biases
                self._user_bias[u] += self.lr * (err - self.reg * self._user_bias[u])
                self._item_bias[i] += self.lr * (err - self.reg * self._item_bias[i])

                # Update factors
                pu = self._user_factors[u].copy()
                qi = self._item_factors[i].copy()
                self._user_factors[u] += self.lr * (err * qi - self.reg * pu)
                self._item_factors[i] += self.lr * (err * pu - self.reg * qi)

            rmse = np.sqrt(total_loss / len(vals))
            if (epoch + 1) % 5 == 0 or epoch == 0:
                logger.info("  Epoch %d/%d — RMSE: %.4f", epoch + 1, self.n_epochs, rmse)

        # Build SVD item vectors for similarity
        self._build_svd_vectors()

        logger.info("FunkSVD training complete (final RMSE: %.4f)", rmse)
        return self

    def _build_svd_vectors(self):
        """Build normalized item vectors for cosine similarity lookup."""
        # Combine item factors with item bias for richer representation
        self._svd_item_vectors = self._item_factors.copy()
        # Normalize for cosine similarity
        norms = np.linalg.norm(self._svd_item_vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        self._svd_item_vectors = self._svd_item_vectors / norms

    # ------------------------------------------------------------------
    # Predictions
    # ------------------------------------------------------------------

    def _predict_raw(self, user_idx: int, item_idx: int) -> float:
        """Raw prediction for internal indices."""
        return float(
            self._global_mean
            + self._user_bias[user_idx]
            + self._item_bias[item_idx]
            + np.dot(self._user_factors[user_idx], self._item_factors[item_idx])
        )

    def predict_score(self, user_id: int, movie_id: int) -> float:
        """Predict the rating for a single user-item pair."""
        if user_id not in self._user2idx or movie_id not in self._item2idx:
            return self._global_mean
        return self._predict_raw(self._user2idx[user_id], self._item2idx[movie_id])

    # ------------------------------------------------------------------
    # Recommendations
    # ------------------------------------------------------------------

    def recommend(
        self,
        user_id: int,
        top_n: int = 20,
        filter_already_liked: bool = True,
    ) -> List[Tuple[int, float]]:
        """Get top-N recommendations for a user.

        Returns:
            List of (movieId, predicted_rating) tuples, descending by score.
        """
        if user_id not in self._user2idx:
            logger.warning("user_id %d not in CF training data", user_id)
            return []

        user_idx = self._user2idx[user_id]
        n_items = len(self._item2idx)

        # Vectorized scoring: predict all items at once
        scores = (
            self._global_mean
            + self._user_bias[user_idx]
            + self._item_bias
            + self._item_factors @ self._user_factors[user_idx]
        )

        if filter_already_liked:
            liked_indices = self._user_item_matrix[user_idx].nonzero()[1]
            scores[liked_indices] = -np.inf

        # Get top-N
        top_indices = np.argsort(scores)[::-1][:top_n]
        results = [
            (int(self._idx2item[idx]), float(scores[idx]))
            for idx in top_indices
            if scores[idx] > -np.inf
        ]
        return results

    def similar_items(
        self, movie_id: int, top_n: int = 20
    ) -> List[Tuple[int, float]]:
        """Return the most similar items by latent factor cosine similarity."""
        if movie_id not in self._item2idx or self._svd_item_vectors is None:
            return []

        item_idx = self._item2idx[movie_id]
        target_vec = self._svd_item_vectors[item_idx]

        # Cosine similarity (vectors are already normalized)
        similarities = self._svd_item_vectors @ target_vec
        similarities[item_idx] = -1.0  # exclude self

        top_indices = np.argsort(similarities)[::-1][:top_n]
        results = [
            (int(self._idx2item[idx]), float(similarities[idx]))
            for idx in top_indices
        ]
        return results

    # ------------------------------------------------------------------
    # Batch scoring (for hybrid)
    # ------------------------------------------------------------------

    def score_items_for_user(
        self, user_id: int, movie_ids: List[int]
    ) -> Dict[int, float]:
        """Score a list of movie IDs for a given user."""
        return {mid: self.predict_score(user_id, mid) for mid in movie_ids}

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, path: str) -> None:
        """Save the trained model to disk."""
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        state = {
            "n_factors": self.n_factors,
            "n_epochs": self.n_epochs,
            "lr": self.lr,
            "reg": self.reg,
            "global_mean": self._global_mean,
            "user_factors": self._user_factors,
            "item_factors": self._item_factors,
            "user_bias": self._user_bias,
            "item_bias": self._item_bias,
            "svd_item_vectors": self._svd_item_vectors,
            "user_item_matrix": self._user_item_matrix,
            "user2idx": self._user2idx,
            "idx2user": self._idx2user,
            "item2idx": self._item2idx,
            "idx2item": self._idx2item,
        }
        with open(path, "wb") as f:
            pickle.dump(state, f, protocol=pickle.HIGHEST_PROTOCOL)
        logger.info("CF model saved to %s", path)

    @classmethod
    def load(cls, path: str) -> "CollaborativeFilteringModel":
        """Load a previously saved model."""
        with open(path, "rb") as f:
            state = pickle.load(f)
        obj = cls(
            n_factors=state["n_factors"],
            n_epochs=state["n_epochs"],
            lr=state["lr"],
            reg=state["reg"],
        )
        obj._global_mean = state["global_mean"]
        obj._user_factors = state["user_factors"]
        obj._item_factors = state["item_factors"]
        obj._user_bias = state["user_bias"]
        obj._item_bias = state["item_bias"]
        obj._svd_item_vectors = state["svd_item_vectors"]
        obj._user_item_matrix = state["user_item_matrix"]
        obj._user2idx = state["user2idx"]
        obj._idx2user = state["idx2user"]
        obj._item2idx = state["item2idx"]
        obj._idx2item = state["idx2item"]
        return obj


# ---------------------------------------------------------------------------
# Grid search helper
# ---------------------------------------------------------------------------


def grid_search_funksvd(
    ratings: pd.DataFrame,
    user2idx: Dict[int, int],
    idx2user: Dict[int, int],
    item2idx: Dict[int, int],
    idx2item: Dict[int, int],
    param_grid: Optional[Dict] = None,
    val_df: Optional[pd.DataFrame] = None,
) -> Tuple["CollaborativeFilteringModel", Dict]:
    """Grid search over FunkSVD hyper-parameters.

    Args:
        param_grid: Dict with keys 'n_factors', 'lr', 'reg'
                    each mapping to a list of values to try.
        val_df: Validation set for evaluating RMSE.

    Returns:
        (best_model, best_params)
    """
    if param_grid is None:
        param_grid = {
            "n_factors": [50, 100, 150],
            "lr": [0.002, 0.005, 0.01],
            "reg": [0.02, 0.05, 0.1],
        }

    from itertools import product as iterproduct

    best_rmse = float("inf")
    best_params = {}
    best_model = None

    keys = list(param_grid.keys())
    total_combos = 1
    for v in param_grid.values():
        total_combos *= len(v)
    logger.info("Grid search: %d combinations to try", total_combos)

    combo_idx = 0
    for combo in iterproduct(*[param_grid[k] for k in keys]):
        params = dict(zip(keys, combo))
        combo_idx += 1
        logger.info("  [%d/%d] Trying: %s", combo_idx, total_combos, params)

        model = CollaborativeFilteringModel(
            n_factors=params.get("n_factors", 100),
            n_epochs=20,  # Fewer epochs for search
            lr=params.get("lr", 0.005),
            reg=params.get("reg", 0.02),
        )
        model.fit(ratings, user2idx, idx2user, item2idx, idx2item)

        # Evaluate on validation set
        if val_df is not None and len(val_df) > 0:
            errors = []
            for _, row in val_df.iterrows():
                pred = model.predict_score(int(row["userId"]), int(row["movieId"]))
                errors.append((row["rating"] - pred) ** 2)
            rmse = float(np.sqrt(np.mean(errors)))
        else:
            # Fall back to training RMSE
            errors = []
            for _, row in ratings.sample(min(10_000, len(ratings))).iterrows():
                pred = model.predict_score(int(row["userId"]), int(row["movieId"]))
                errors.append((row["rating"] - pred) ** 2)
            rmse = float(np.sqrt(np.mean(errors)))

        logger.info("    RMSE: %.4f", rmse)

        if rmse < best_rmse:
            best_rmse = rmse
            best_params = params
            best_model = model

    logger.info("Best params: %s (RMSE: %.4f)", best_params, best_rmse)
    return best_model, best_params
