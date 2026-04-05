"""
Tests for the FastAPI endpoints and core model logic.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.evaluation.metrics import (
    average_precision,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)


# ---------------------------------------------------------------------------
# Metric unit tests
# ---------------------------------------------------------------------------


class TestPrecisionAtK:
    def test_perfect(self):
        rec = [1, 2, 3, 4, 5]
        rel = {1, 2, 3, 4, 5}
        assert precision_at_k(rec, rel, 5) == 1.0

    def test_none_relevant(self):
        rec = [1, 2, 3]
        rel = {10, 20}
        assert precision_at_k(rec, rel, 3) == 0.0

    def test_partial(self):
        rec = [1, 2, 3, 4, 5]
        rel = {2, 4}
        assert precision_at_k(rec, rel, 5) == 0.4

    def test_k_zero(self):
        assert precision_at_k([1], {1}, 0) == 0.0


class TestRecallAtK:
    def test_perfect(self):
        rec = [1, 2, 3]
        rel = {1, 2, 3}
        assert recall_at_k(rec, rel, 3) == 1.0

    def test_partial(self):
        rec = [1, 2, 3]
        rel = {1, 2, 3, 4, 5, 6}
        assert recall_at_k(rec, rel, 3) == 0.5

    def test_empty_relevant(self):
        assert recall_at_k([1, 2], set(), 2) == 0.0


class TestNDCG:
    def test_perfect(self):
        rec = [1, 2, 3]
        rel = {1, 2, 3}
        assert ndcg_at_k(rec, rel, 3) == 1.0

    def test_imperfect_order(self):
        rec = [10, 1, 2]  # 10 is not relevant
        rel = {1, 2}
        score = ndcg_at_k(rec, rel, 3)
        assert 0 < score < 1.0

    def test_empty(self):
        assert ndcg_at_k([], {1}, 5) == 0.0


class TestAveragePrecision:
    def test_perfect(self):
        rec = [1, 2, 3]
        rel = {1, 2, 3}
        assert average_precision(rec, rel, 3) == 1.0

    def test_single_hit(self):
        rec = [10, 20, 1]
        rel = {1}
        ap = average_precision(rec, rel, 3)
        # hit at position 3, precision = 1/3
        assert abs(ap - (1 / 3)) < 1e-6


# ---------------------------------------------------------------------------
# Data pipeline unit tests
# ---------------------------------------------------------------------------


class TestPreprocessing:
    def test_create_id_mappings(self):
        import pandas as pd
        from src.data_pipeline.preprocessing import create_id_mappings

        df = pd.DataFrame({
            "userId": [10, 20, 10, 30],
            "movieId": [100, 200, 200, 300],
            "rating": [4.0, 3.0, 5.0, 2.0],
        })
        u2i, i2u, it2i, i2it = create_id_mappings(df)
        assert len(u2i) == 3  # 3 unique users
        assert len(it2i) == 3  # 3 unique items
        assert i2u[u2i[10]] == 10

    def test_user_stratified_split(self):
        import pandas as pd
        from src.data_pipeline.preprocessing import user_stratified_split

        rows = []
        for uid in range(1, 11):
            for i in range(20):
                rows.append({"userId": uid, "movieId": i + 1, "rating": 4.0})
        df = pd.DataFrame(rows)

        train, val, test = user_stratified_split(df)
        # Every user should appear in training
        assert set(train["userId"].unique()) == set(range(1, 11))
        # Total should be preserved
        assert len(train) + len(val) + len(test) == len(df)


# ---------------------------------------------------------------------------
# Content-based model unit tests
# ---------------------------------------------------------------------------


class TestContentBasedModel:
    def test_fit_and_similar(self):
        import pandas as pd
        from src.models.content_based import ContentBasedModel

        movies = pd.DataFrame({
            "movieId": [1, 2, 3],
            "title": ["Toy Story", "Jurassic Park", "Toy Story 2"],
            "genres": ["Animation|Comedy", "Action|Sci-Fi", "Animation|Comedy"],
            "combined_text": [
                "animation comedy toy kids",
                "action science fiction dinosaur",
                "animation comedy toy kids sequel",
            ],
        })

        model = ContentBasedModel(max_features=100)
        model.fit(movies)

        # Toy Story should be more similar to Toy Story 2 than Jurassic Park
        sims = model.similar_items(1, top_n=2)
        assert len(sims) == 2
        sim_ids = [mid for mid, _ in sims]
        assert sim_ids[0] == 3  # Toy Story 2 should be most similar


# ---------------------------------------------------------------------------
# API endpoint tests (if httpx is available)
# ---------------------------------------------------------------------------

try:
    from httpx import AsyncClient, ASGITransport

    # Note: These tests require data to be present in data/raw/
    # They are skipped if data is not available.

    @pytest.mark.skipif(
        not os.path.exists("data/raw/ratings.csv")
        and not os.path.exists("data/raw/ratings.dat"),
        reason="MovieLens data not found in data/raw/",
    )
    class TestAPIEndpoints:
        @pytest.fixture
        def anyio_backend(self):
            return "asyncio"

        @pytest.mark.anyio
        async def test_health(self):
            from src.api.main import app

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/health")
                assert resp.status_code == 200
                assert resp.json()["status"] == "ok"

except ImportError:
    pass
