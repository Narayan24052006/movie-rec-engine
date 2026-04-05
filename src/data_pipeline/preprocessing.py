"""
Data Preprocessing Module
==========================
Implements user-stratified train/validation/test splitting and
ID-mapping utilities needed by the recommendation models.
"""

import logging
from typing import Dict, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# ID Mappers — needed to convert sparse movie/user IDs into contiguous indices
# ---------------------------------------------------------------------------


def create_id_mappings(
    ratings: pd.DataFrame,
) -> Tuple[Dict[int, int], Dict[int, int], Dict[int, int], Dict[int, int]]:
    """Create bidirectional mappings for user and item IDs.

    Returns:
        (user2idx, idx2user, item2idx, idx2item)
    """
    unique_users = sorted(ratings["userId"].unique())
    unique_items = sorted(ratings["movieId"].unique())

    user2idx = {uid: idx for idx, uid in enumerate(unique_users)}
    idx2user = {idx: uid for uid, idx in user2idx.items()}

    item2idx = {iid: idx for idx, iid in enumerate(unique_items)}
    idx2item = {idx: iid for iid, idx in item2idx.items()}

    logger.info(
        "ID mappings created — %d users, %d items", len(user2idx), len(item2idx)
    )
    return user2idx, idx2user, item2idx, idx2item


# ---------------------------------------------------------------------------
# User-Stratified Splitting
# ---------------------------------------------------------------------------


def user_stratified_split(
    ratings: pd.DataFrame,
    train_frac: float = 0.70,
    val_frac: float = 0.15,
    test_frac: float = 0.15,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split ratings into train / validation / test sets **per user**.

    For each user we sort by timestamp (if available) and assign the
    first ``train_frac`` interactions to train, the next ``val_frac``
    to validation, and the rest to test.  This prevents data leakage
    and guarantees every user appears in the training set.

    Args:
        ratings: Must contain at least ``userId`` and ``rating`` columns.
                 A ``timestamp`` column is used for chronological ordering
                 when present.
        train_frac: Fraction of each user's ratings for training.
        val_frac: Fraction for validation.
        test_frac: Fraction for testing.
        random_state: Seed for reproducibility when no timestamp exists.

    Returns:
        (train_df, val_df, test_df)
    """
    assert abs(train_frac + val_frac + test_frac - 1.0) < 1e-6, (
        "Fractions must sum to 1.0"
    )

    rng = np.random.RandomState(random_state)
    train_parts, val_parts, test_parts = [], [], []

    has_timestamp = "timestamp" in ratings.columns

    for _uid, group in ratings.groupby("userId"):
        if has_timestamp:
            group = group.sort_values("timestamp")
        else:
            group = group.sample(frac=1.0, random_state=rng)

        n = len(group)
        n_train = max(1, int(n * train_frac))  # at least 1 in train
        n_val = max(0, int(n * val_frac))

        train_parts.append(group.iloc[:n_train])
        val_parts.append(group.iloc[n_train : n_train + n_val])
        test_parts.append(group.iloc[n_train + n_val :])

    train_df = pd.concat(train_parts, ignore_index=True)
    val_df = pd.concat(val_parts, ignore_index=True)
    test_df = pd.concat(test_parts, ignore_index=True)

    logger.info(
        "User-stratified split: train=%d  val=%d  test=%d",
        len(train_df),
        len(val_df),
        len(test_df),
    )
    return train_df, val_df, test_df


# ---------------------------------------------------------------------------
# Popularity & recency helpers
# ---------------------------------------------------------------------------


def compute_item_popularity(ratings: pd.DataFrame) -> pd.Series:
    """Return a Series indexed by movieId with the number of ratings."""
    return ratings.groupby("movieId")["rating"].count().rename("popularity")


def compute_item_avg_rating(ratings: pd.DataFrame) -> pd.Series:
    """Return a Series indexed by movieId with the mean rating."""
    return ratings.groupby("movieId")["rating"].mean().rename("avg_rating")


def compute_item_recency(ratings: pd.DataFrame) -> pd.Series:
    """Return a Series indexed by movieId with the latest timestamp.
    Useful for recency-based re-ranking.  Returns NaN-filled series if
    no timestamp column exists.
    """
    if "timestamp" not in ratings.columns:
        return pd.Series(dtype=np.float64, name="recency")
    return ratings.groupby("movieId")["timestamp"].max().rename("recency")
