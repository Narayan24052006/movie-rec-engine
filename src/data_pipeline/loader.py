"""
Data Loader Module
==================
Handles loading and memory-optimized ingestion of the MovieLens dataset.
Supports both MovieLens 1M and MovieLens Latest (small/full) formats.
"""

import os
import logging
from typing import Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Type-optimization helpers
# ---------------------------------------------------------------------------

_INT_DOWNCAST = {"userId": np.int32, "movieId": np.int32}
_FLOAT_DOWNCAST = {"rating": np.float32}


def _optimize_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Down-cast numeric columns to save memory."""
    for col, dtype in _INT_DOWNCAST.items():
        if col in df.columns:
            df[col] = df[col].astype(dtype)
    for col, dtype in _FLOAT_DOWNCAST.items():
        if col in df.columns:
            df[col] = df[col].astype(dtype)
    return df


# ---------------------------------------------------------------------------
# Individual loaders
# ---------------------------------------------------------------------------


def load_ratings(data_dir: str) -> pd.DataFrame:
    """Load ratings.csv with optimized dtypes.

    Handles both comma-separated and '::'-separated (ML-1M) formats.
    """
    path = os.path.join(data_dir, "ratings.csv")
    if not os.path.exists(path):
        # Try ML-1M .dat format
        dat_path = os.path.join(data_dir, "ratings.dat")
        if os.path.exists(dat_path):
            df = pd.read_csv(
                dat_path,
                sep="::",
                engine="python",
                names=["userId", "movieId", "rating", "timestamp"],
            )
        else:
            raise FileNotFoundError(
                f"No ratings file found in {data_dir}. "
                "Expected ratings.csv or ratings.dat"
            )
    else:
        df = pd.read_csv(path)

    df = _optimize_dtypes(df)
    logger.info("Loaded %d ratings", len(df))
    return df


def load_movies(data_dir: str) -> pd.DataFrame:
    """Load movies.csv (or movies.dat for ML-1M).

    Returns DataFrame with columns: movieId, title, genres (pipe-separated str).
    """
    path = os.path.join(data_dir, "movies.csv")
    if not os.path.exists(path):
        dat_path = os.path.join(data_dir, "movies.dat")
        if os.path.exists(dat_path):
            df = pd.read_csv(
                dat_path,
                sep="::",
                engine="python",
                names=["movieId", "title", "genres"],
                encoding="latin-1",
            )
        else:
            raise FileNotFoundError(
                f"No movies file found in {data_dir}. "
                "Expected movies.csv or movies.dat"
            )
    else:
        df = pd.read_csv(path)

    df["movieId"] = df["movieId"].astype(np.int32)
    logger.info("Loaded %d movies", len(df))
    return df


def load_tags(data_dir: str) -> Optional[pd.DataFrame]:
    """Load tags.csv if available. Returns None if the file does not exist."""
    path = os.path.join(data_dir, "tags.csv")
    if not os.path.exists(path):
        dat_path = os.path.join(data_dir, "tags.dat")
        if os.path.exists(dat_path):
            df = pd.read_csv(
                dat_path,
                sep="::",
                engine="python",
                names=["userId", "movieId", "tag", "timestamp"],
                encoding="latin-1",
            )
        else:
            logger.warning("No tags file found in %s — skipping tags.", data_dir)
            return None
    else:
        df = pd.read_csv(path)

    df = _optimize_dtypes(df)
    # Ensure tag column is string
    df["tag"] = df["tag"].astype(str).str.strip()
    logger.info("Loaded %d tags", len(df))
    return df


# ---------------------------------------------------------------------------
# Merged dataset builder
# ---------------------------------------------------------------------------


def build_merged_dataset(
    data_dir: str,
) -> Tuple[pd.DataFrame, pd.DataFrame, Optional[pd.DataFrame]]:
    """Load all tables, merge tags into movies, and return
    (ratings_df, movies_df, tags_df).

    ``movies_df`` will have an extra column ``tag_str`` containing
    space-joined tags per movie (useful for TF-IDF later).
    """
    ratings = load_ratings(data_dir)
    movies = load_movies(data_dir)
    tags = load_tags(data_dir)

    # Aggregate tags per movie into a single string
    if tags is not None:
        tag_agg = (
            tags.groupby("movieId")["tag"]
            .apply(lambda x: " ".join(x))
            .reset_index()
            .rename(columns={"tag": "tag_str"})
        )
        movies = movies.merge(tag_agg, on="movieId", how="left")
    else:
        movies["tag_str"] = ""

    movies["tag_str"] = movies["tag_str"].fillna("")

    # Build a combined text column for content features
    movies["combined_text"] = (
        movies["genres"].str.replace("|", " ", regex=False)
        + " "
        + movies["tag_str"]
    )

    logger.info(
        "Merged dataset ready — %d ratings, %d movies", len(ratings), len(movies)
    )
    return ratings, movies, tags
