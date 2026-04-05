"""
Evaluation Module
==================
Computes offline metrics: Precision@k, Recall@k, nDCG@k, MAP
for standalone and hybrid models.

Can be run as a script or imported for use in a Jupyter notebook.
"""

import logging
import sys
import os
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Core metric functions
# ---------------------------------------------------------------------------


def precision_at_k(
    recommended: List[int], relevant: set, k: int = 10
) -> float:
    """Precision@k: fraction of top-k recommendations that are relevant."""
    if k <= 0:
        return 0.0
    rec_at_k = recommended[:k]
    hits = sum(1 for r in rec_at_k if r in relevant)
    return hits / k


def recall_at_k(
    recommended: List[int], relevant: set, k: int = 10
) -> float:
    """Recall@k: fraction of relevant items found in top-k recommendations."""
    if not relevant:
        return 0.0
    rec_at_k = recommended[:k]
    hits = sum(1 for r in rec_at_k if r in relevant)
    return hits / len(relevant)


def ndcg_at_k(
    recommended: List[int], relevant: set, k: int = 10
) -> float:
    """Normalized Discounted Cumulative Gain at k."""
    if not relevant or k <= 0:
        return 0.0

    rec_at_k = recommended[:k]

    # DCG
    dcg = 0.0
    for i, item in enumerate(rec_at_k):
        if item in relevant:
            dcg += 1.0 / np.log2(i + 2)  # i+2 because log2(1) = 0

    # Ideal DCG
    n_rel = min(len(relevant), k)
    idcg = sum(1.0 / np.log2(i + 2) for i in range(n_rel))

    return dcg / idcg if idcg > 0 else 0.0


def average_precision(
    recommended: List[int], relevant: set, k: int = 10
) -> float:
    """Average Precision at k for a single user."""
    if not relevant:
        return 0.0

    rec_at_k = recommended[:k]
    score = 0.0
    hits = 0

    for i, item in enumerate(rec_at_k):
        if item in relevant:
            hits += 1
            score += hits / (i + 1)

    return score / min(len(relevant), k)


def mean_average_precision(
    all_recommended: Dict[int, List[int]],
    all_relevant: Dict[int, set],
    k: int = 10,
) -> float:
    """Mean Average Precision across all users."""
    aps = []
    for user_id in all_recommended:
        if user_id in all_relevant and all_relevant[user_id]:
            ap = average_precision(
                all_recommended[user_id], all_relevant[user_id], k
            )
            aps.append(ap)
    return float(np.mean(aps)) if aps else 0.0


# ---------------------------------------------------------------------------
# Full evaluation pipeline
# ---------------------------------------------------------------------------


def evaluate_model(
    recommend_fn,
    test_df: pd.DataFrame,
    train_df: pd.DataFrame,
    k_values: List[int] = None,
    model_name: str = "Model",
    n_users_sample: int = 500,
    random_state: int = 42,
) -> pd.DataFrame:
    """Evaluate a recommendation model across multiple k values.

    Args:
        recommend_fn: Callable(user_id, top_n) -> List[int] of movieIds
        test_df: Test ratings (ground truth)
        train_df: Training ratings (to know what user has seen)
        k_values: List of k values to evaluate
        model_name: Name for this model in results
        n_users_sample: Number of users to sample for evaluation
        random_state: Random seed

    Returns:
        DataFrame with metric results per k
    """
    if k_values is None:
        k_values = [5, 10, 20]

    # Build ground truth: relevant items per user (rating >= 3.5 in test)
    relevant_items = (
        test_df[test_df["rating"] >= 3.5]
        .groupby("userId")["movieId"]
        .apply(set)
        .to_dict()
    )

    # Sample users who have test data
    eligible_users = [uid for uid in relevant_items if relevant_items[uid]]
    rng = np.random.RandomState(random_state)
    sample_users = rng.choice(
        eligible_users,
        size=min(n_users_sample, len(eligible_users)),
        replace=False,
    )

    logger.info(
        "Evaluating %s on %d users...", model_name, len(sample_users)
    )

    results = []
    for k in k_values:
        precisions, recalls, ndcgs, aps = [], [], [], []

        for user_id in sample_users:
            try:
                recs = recommend_fn(int(user_id), top_n=k)
            except Exception as e:
                logger.debug("Error recommending for user %d: %s", user_id, e)
                continue

            rel = relevant_items.get(user_id, set())
            if not rel:
                continue

            precisions.append(precision_at_k(recs, rel, k))
            recalls.append(recall_at_k(recs, rel, k))
            ndcgs.append(ndcg_at_k(recs, rel, k))
            aps.append(average_precision(recs, rel, k))

        results.append(
            {
                "model": model_name,
                "k": k,
                "Precision@k": round(float(np.mean(precisions)), 4) if precisions else 0.0,
                "Recall@k": round(float(np.mean(recalls)), 4) if recalls else 0.0,
                "nDCG@k": round(float(np.mean(ndcgs)), 4) if ndcgs else 0.0,
                "MAP@k": round(float(np.mean(aps)), 4) if aps else 0.0,
                "n_users": len(precisions),
            }
        )
        logger.info(
            "  %s @ k=%d: P=%.4f R=%.4f nDCG=%.4f MAP=%.4f (%d users)",
            model_name,
            k,
            results[-1]["Precision@k"],
            results[-1]["Recall@k"],
            results[-1]["nDCG@k"],
            results[-1]["MAP@k"],
            results[-1]["n_users"],
        )

    return pd.DataFrame(results)


# ---------------------------------------------------------------------------
# Plotting helpers (for notebook / script usage)
# ---------------------------------------------------------------------------


def plot_comparison(
    results_df: pd.DataFrame,
    save_path: str = None,
) -> None:
    """Plot metric comparison across models.

    Args:
        results_df: DataFrame with columns [model, k, Precision@k, Recall@k, nDCG@k, MAP@k]
        save_path: If provided, save plot to this path
    """
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
    except ImportError:
        logger.warning("matplotlib/seaborn not installed — skipping plots")
        return

    metrics = ["Precision@k", "Recall@k", "nDCG@k", "MAP@k"]
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Model Comparison: Offline Metrics", fontsize=16, fontweight="bold")

    palette = sns.color_palette("husl", n_colors=results_df["model"].nunique())

    for ax, metric in zip(axes.flat, metrics):
        for i, model in enumerate(results_df["model"].unique()):
            model_data = results_df[results_df["model"] == model]
            ax.plot(
                model_data["k"],
                model_data[metric],
                marker="o",
                label=model,
                color=palette[i],
                linewidth=2,
            )
        ax.set_xlabel("k")
        ax.set_ylabel(metric)
        ax.set_title(metric)
        ax.legend()
        ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        logger.info("Plot saved to %s", save_path)

    plt.close()


# ---------------------------------------------------------------------------
# Main evaluation script
# ---------------------------------------------------------------------------


def run_full_evaluation(data_dir: str, output_dir: str = "data/processed"):
    """Run the complete evaluation pipeline and save results."""
    from src.data_pipeline.loader import build_merged_dataset
    from src.data_pipeline.preprocessing import (
        create_id_mappings,
        user_stratified_split,
    )
    from src.models.content_based import ContentBasedModel
    from src.models.collaborative_filtering import CollaborativeFilteringModel
    from src.models.hybrid import HybridRecommender
    from src.data_pipeline.preprocessing import (
        compute_item_popularity,
        compute_item_recency,
        compute_item_avg_rating,
    )

    logging.basicConfig(level=logging.INFO)

    # Load data
    ratings, movies, tags = build_merged_dataset(data_dir)
    user2idx, idx2user, item2idx, idx2item = create_id_mappings(ratings)
    train_df, val_df, test_df = user_stratified_split(ratings)

    # --- Train CBF ---
    cbf = ContentBasedModel(max_features=10_000)
    cbf.fit(movies)

    def cbf_recommend(user_id, top_n=20):
        liked = (
            train_df[train_df["userId"] == user_id]["movieId"].tolist()
        )
        recs = cbf.get_content_scores_for_user(liked, top_n=top_n)
        return [mid for mid, _ in recs]

    # --- Train CF ---
    cf = CollaborativeFilteringModel(factors=128, regularization=0.01, iterations=30)
    cf.fit(train_df, user2idx, idx2user, item2idx, idx2item)

    def cf_recommend(user_id, top_n=20):
        recs = cf.recommend(user_id, top_n=top_n)
        return [mid for mid, _ in recs]

    # --- Build Hybrid ---
    popularity = compute_item_popularity(train_df)
    recency = compute_item_recency(train_df)
    avg_rating = compute_item_avg_rating(train_df)

    hybrid = HybridRecommender(cf_model=cf, cbf_model=cbf)
    hybrid.set_item_metadata(
        popularity=popularity,
        recency=recency,
        avg_rating=avg_rating,
        all_movie_ids=list(item2idx.keys()),
    )

    def hybrid_recommend(user_id, top_n=20):
        recs = hybrid.recommend(user_id, top_n=top_n)
        return [r["movieId"] for r in recs]

    # --- Evaluate all models ---
    all_results = []
    for name, fn in [
        ("Content-Based", cbf_recommend),
        ("Collaborative (ALS)", cf_recommend),
        ("Hybrid", hybrid_recommend),
    ]:
        df = evaluate_model(
            fn, test_df, train_df, k_values=[5, 10, 20], model_name=name
        )
        all_results.append(df)

    results_df = pd.concat(all_results, ignore_index=True)

    # Save results
    os.makedirs(output_dir, exist_ok=True)
    results_path = os.path.join(output_dir, "evaluation_results.csv")
    results_df.to_csv(results_path, index=False)
    logger.info("Results saved to %s", results_path)

    # Print results table
    print("\n" + "=" * 70)
    print("EVALUATION RESULTS")
    print("=" * 70)
    print(results_df.to_string(index=False))
    print("=" * 70)

    # Plot
    plot_path = os.path.join(output_dir, "model_comparison.png")
    plot_comparison(results_df, save_path=plot_path)

    return results_df


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate recommendation models")
    parser.add_argument(
        "--data-dir",
        default="data/raw",
        help="Path to raw MovieLens data",
    )
    parser.add_argument(
        "--output-dir",
        default="data/processed",
        help="Path to save evaluation results",
    )
    args = parser.parse_args()
    run_full_evaluation(args.data_dir, args.output_dir)
