"""
FastAPI Application — Movie Recommendation Engine
===================================================
Serves hybrid recommendations, similar items, and explanations.
Models are loaded once at startup for sub-100ms response times.
"""

import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware

# Ensure the project root is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import json
from src.api.database import init_db, create_user, is_username_taken, get_user_by_username, get_user_by_id, seed_existing_users, seed_admin, update_user_genres, add_to_wishlist, remove_from_wishlist, get_user_wishlist, is_in_wishlist, get_all_users, delete_user, promote_user_to_admin, demote_admin_to_user, get_all_movies_from_db, delete_movie
from src.api.auth import get_password_hash, verify_password, create_access_token, get_current_user, validate_email, validate_password
from src.api.data_downloader import download_movielens_data

from src.api.schemas import (
    ExplanationResponse,
    HealthResponse,
    RecommendationItem,
    RecommendationResponse,
    SimilarItemResponse,
    UserQuizRequest,
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserProfileResponse,
)


from src.data_pipeline.loader import build_merged_dataset
from src.data_pipeline.preprocessing import (
    compute_item_avg_rating,
    compute_item_popularity,
    compute_item_recency,
    create_id_mappings,
    user_stratified_split,
)
from src.models.cold_start import ColdStartHandler
from src.models.collaborative_filtering import CollaborativeFilteringModel
from src.models.content_based import ContentBasedModel
from src.models.hybrid import HybridRecommender

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Global model references (populated at startup)
# ---------------------------------------------------------------------------

_hybrid: Optional[HybridRecommender] = None
_cold_start: Optional[ColdStartHandler] = None
_cbf: Optional[ContentBasedModel] = None
_cf: Optional[CollaborativeFilteringModel] = None
_movies_df = None
_known_users: set = set()
_known_items: set = set()
_movie_lookup = {}  # movieId -> {title, genres}

DATA_DIR = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw"))
MODEL_DIR = os.environ.get("MODEL_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed"))


# ---------------------------------------------------------------------------
# Lifespan: load models once at startup
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _hybrid, _cold_start, _cbf, _cf, _movies_df
    global _known_users, _known_items, _movie_lookup

    logger.info("Initializing PostgreSQL Database...")
    init_db()

    logger.info("Creating default admin user...")
    seed_admin(lambda p: get_password_hash(p, skip_validation=True))

    # Attempt to download MovieLens data if not present (for Render deployment)
    logger.info("Checking for MovieLens data...")
    if not download_movielens_data():
        logger.warning("⚠️ Could not download MovieLens data. Models will not be available.")

    logger.info("Loading data from %s ...", DATA_DIR)

    try:
        # 1. Load data
        ratings, movies, _tags = build_merged_dataset(DATA_DIR)
        _movies_df = movies

        # Build movie lookup for enrichment
        for _, row in movies.iterrows():
            _movie_lookup[int(row["movieId"])] = {
                "title": str(row["title"]),
                "genres": str(row.get("genres", "")).replace("(no genres listed)", ""),
            }

        # 2. Preprocess
        user2idx, idx2user, item2idx, idx2item = create_id_mappings(ratings)
        train_df, _val_df, _test_df = user_stratified_split(ratings)

        # Convert to native Python ints to avoid JSON serialization issues with numpy.int32
        _known_users = {int(uid) for uid in user2idx.keys()}
        _known_items = {int(iid) for iid in item2idx.keys()}

        logger.info(f"Seeding {len(_known_users)} existing users into PostgreSQL...")
        seed_existing_users(_known_users, lambda p: get_password_hash(p, skip_validation=True))

        # 3. Train Content-Based model
        logger.info("Training Content-Based model...")
        _cbf = ContentBasedModel(max_features=10_000, ngram_range=(1, 2))
        _cbf.fit(movies)

        # 4. Train Collaborative Filtering model
        cf_model_path = os.path.join(MODEL_DIR, "cf_model.pkl")
        if os.path.exists(cf_model_path):
            logger.info("Loading pre-trained CF model from %s", cf_model_path)
            _cf = CollaborativeFilteringModel.load(cf_model_path)
        else:
            logger.info("Training Collaborative Filtering model (ALS)...")
            _cf = CollaborativeFilteringModel(
                n_factors=128, n_epochs=30, lr=0.005, reg=0.02
            )
            _cf.fit(train_df, user2idx, idx2user, item2idx, idx2item)
            os.makedirs(MODEL_DIR, exist_ok=True)
            _cf.save(cf_model_path)
            logger.info("CF model saved to %s", cf_model_path)

        # 5. Build Hybrid
        popularity = compute_item_popularity(train_df)
        recency = compute_item_recency(train_df)
        avg_rating = compute_item_avg_rating(train_df)

        _hybrid = HybridRecommender(
            cf_model=_cf, cbf_model=_cbf,
            w_cf=0.50, w_cbf=0.30, w_pop=0.10, w_rec=0.10,
        )
        _hybrid.set_item_metadata(
            popularity=popularity,
            recency=recency,
            avg_rating=avg_rating,
            all_movie_ids=list(item2idx.keys()),
        )

        # 6. Cold-start handler
        _cold_start = ColdStartHandler(
            cbf_model=_cbf,
            movies_df=movies,
            popularity=popularity.to_dict(),
        )

        logger.info("All models loaded and ready to serve!")
    except FileNotFoundError as e:
        logger.warning(f"⚠️ Data files not found: {e}")
        logger.warning("Starting without recommendation models. Admin & auth features will work.")
        logger.warning("This is normal on deployment servers without data files.")

    yield
    logger.info("Shutting down recommendation engine.")


# ---------------------------------------------------------------------------
# App creation
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Movie Recommendation Engine",
    description="Hybrid recommender with CF, CBF, cold-start handling, and explanations.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Helper to enrich recommendations with movie metadata
# ---------------------------------------------------------------------------


def _enrich(items: list) -> list:
    """Add title and genres from lookup to recommendation dicts."""
    for item in items:
        mid = item.get("movieId", item.get("movie_id"))
        if mid and mid in _movie_lookup:
            item["title"] = _movie_lookup[mid]["title"]
            item["genres"] = _movie_lookup[mid]["genres"]
    return items


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="ok",
        model_loaded=_hybrid is not None,
        n_users=len(_known_users),
        n_items=len(_known_items),
    )

# ---------------------------------------------------------------------------
# Auth Endpoints
# ---------------------------------------------------------------------------

@app.post("/auth/register", response_model=UserProfileResponse)
async def register(user: UserRegisterRequest):
    # Validate email domain and password strength
    if not validate_email(user.username):
        raise HTTPException(status_code=400, detail="Only Gmail accounts are allowed")
    if not validate_password(user.password):
        raise HTTPException(status_code=400, detail="Password does not meet complexity requirements")
    if is_username_taken(user.username):
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_pass = get_password_hash(user.password)
    new_user = create_user(
        username=user.username,
        password_hash=hashed_pass,
        preferred_genres=user.preferred_genres,
        is_admin=False
    )
    if not new_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Parse JSON string back to list for response schema
    new_user["preferred_genres"] = json.loads(new_user["preferred_genres"])
    return new_user

@app.post("/auth/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Enforce Gmail domain for login
    if not validate_email(form_data.username):
        raise HTTPException(status_code=400, detail="Only Gmail accounts are allowed")
    user_dict = get_user_by_username(form_data.username)
    if not user_dict or not verify_password(form_data.password, user_dict["password_hash"]):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": user_dict["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/me", response_model=UserProfileResponse)
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    user_copy = dict(current_user)
    user_copy["preferred_genres"] = json.loads(user_copy["preferred_genres"])
    return user_copy


@app.get("/recommendations/{user_id}", response_model=RecommendationResponse)
async def get_recommendations(
    user_id: int,
    top_n: int = Query(default=20, ge=1, le=100),
):
    """Get Top-N hybrid recommendations for a user."""
    if _hybrid is None:
        raise HTTPException(status_code=503, detail="Models not loaded yet")

    is_cold = _cold_start.is_cold_start_user(user_id, _known_users)

    if is_cold:
        # 1. Attempt to fetch genres from DB if they are a registered new user
        db_user = get_user_by_id(user_id)
        if db_user and db_user.get("preferred_genres") and db_user["preferred_genres"] != "[]":
            genres = json.loads(db_user["preferred_genres"])
            if genres:
                recs = _cold_start.process_user_quiz(genres, top_n)
                items = [
                    RecommendationItem(
                        movieId=int(r["movieId"]),
                        title=str(r.get("title", "")),
                        genres=str(r.get("genres", "")),
                        score=float(r.get("score", 0.0)),
                        source="cold_start_quiz",
                    )
                    for r in recs
                ]
                return RecommendationResponse(user_id=user_id, recommendations=items, is_cold_start=True, total=len(items))

        # 2. Return popular movies for completely unknown users (or registered users with no genres)
        recs = _cold_start._popular_movies_fallback(top_n)
        items = [
            RecommendationItem(
                movieId=int(r["movieId"]),
                title=str(r.get("title", "")),
                genres=str(r.get("genres", "")),
                score=float(r.get("score", 0.0)),
                source="popularity_fallback",
            )
            for r in recs
        ]
    else:
        raw_recs = _hybrid.recommend(user_id, top_n=top_n)
        raw_recs = _enrich(raw_recs)
        items = [
            RecommendationItem(
                movieId=int(r["movieId"]),
                title=str(r.get("title", "")),
                genres=str(r.get("genres", "")),
                score=float(r.get("score", 0.0)),
                cf_score=float(r.get("cf_score", 0.0)),
                cbf_score=float(r.get("cbf_score", 0.0)),
                pop_score=float(r.get("pop_score", 0.0)),
                rec_score=float(r.get("rec_score", 0.0)),
                source="hybrid",
            )
            for r in raw_recs
        ]

    return RecommendationResponse(
        user_id=user_id,
        recommendations=items,
        is_cold_start=is_cold,
        total=len(items),
    )


@app.get("/similar-items/{item_id}", response_model=SimilarItemResponse)
async def get_similar_items(
    item_id: int,
    top_n: int = Query(default=20, ge=1, le=100),
):
    """Get items similar to the specified movie."""
    if _cbf is None:
        raise HTTPException(status_code=503, detail="Models not loaded yet")

    title = _movie_lookup.get(item_id, {}).get("title", "Unknown")

    # Try CF-based similarity first, fall back to CBF
    is_cold_item = _cold_start.is_cold_start_item(item_id, _known_items)

    if is_cold_item:
        recs = _cold_start.recommend_new_item_similar(item_id, top_n=top_n)
        items = [
            RecommendationItem(
                movieId=int(r["movieId"]),
                title=str(r.get("title", "")),
                genres=str(r.get("genres", "")),
                score=float(r.get("similarity", 0.0)),
                source="content_fallback",
            )
            for r in recs
        ]
    else:
        # Blend CF and CBF similar items
        cf_similar = _cf.similar_items(item_id, top_n=top_n)
        cbf_similar = _cbf.similar_items(item_id, top_n=top_n)

        combined = {}
        for mid, score in cf_similar:
            combined[int(mid)] = {"cf": float(score), "cbf": 0.0}
        for mid, score in cbf_similar:
            mid = int(mid)
            if mid in combined:
                combined[mid]["cbf"] = float(score)
            else:
                combined[mid] = {"cf": 0.0, "cbf": float(score)}

        merged = []
        for mid, scores in combined.items():
            final = 0.6 * scores["cf"] + 0.4 * scores["cbf"]
            info = _movie_lookup.get(mid, {})
            merged.append(
                RecommendationItem(
                    movieId=int(mid),
                    title=str(info.get("title", "")),
                    genres=str(info.get("genres", "")),
                    score=round(final, 4),
                    cf_score=round(scores["cf"], 4),
                    cbf_score=round(scores["cbf"], 4),
                    source="hybrid_similar",
                )
            )
        merged.sort(key=lambda x: x.score, reverse=True)
        items = merged[:top_n]

    return SimilarItemResponse(
        movie_id=item_id,
        title=title,
        similar_items=items,
    )


@app.get("/explain/{user_id}/{item_id}", response_model=ExplanationResponse)
async def explain_recommendation(user_id: int, item_id: int):
    """Explain why a movie was recommended to a user."""
    if _hybrid is None:
        raise HTTPException(status_code=503, detail="Models not loaded yet")

    explanation = _hybrid.explain(user_id, item_id)
    return ExplanationResponse(**explanation)


@app.post("/quiz", response_model=RecommendationResponse)
async def process_quiz(quiz: UserQuizRequest):
    """Handle a new-user cold-start quiz submission."""
    if _cold_start is None:
        raise HTTPException(status_code=503, detail="Models not loaded yet")

    recs = _cold_start.process_user_quiz(
        preferred_genres=quiz.preferred_genres,
        top_n=quiz.top_n,
    )
    items = [
        RecommendationItem(
            movieId=int(r["movieId"]),
            title=str(r.get("title", "")),
            genres=str(r.get("genres", "")),
            score=float(r.get("score", 0.0)),
            source=str(r.get("source", "cold_start_quiz")),
        )
        for r in recs
    ]

    return RecommendationResponse(
        user_id=0,  # New user, no ID yet
        recommendations=items,
        is_cold_start=True,
        total=len(items),
    )


@app.get("/movies")
async def list_movies(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    search: str = Query(default=""),
):
    """List movies in the catalogue (for UI browsing)."""
    if _movies_df is None:
        raise HTTPException(status_code=503, detail="Data not loaded yet")

    df = _movies_df
    if search:
        df = df[df["title"].str.contains(search, case=False, na=False)]

    subset = df.iloc[offset : offset + limit]
    return {
        "total": len(df),
        "offset": offset,
        "limit": limit,
        "movies": [
            {
                "movieId": int(row["movieId"]),
                "title": str(row["title"]),
                "genres": str(row.get("genres", "")).replace("(no genres listed)", ""),
            }
            for _, row in subset.iterrows()
        ],
    }


@app.get("/users")
async def list_users(limit: int = Query(default=50, ge=1, le=500)):
    """List known user IDs (for testing in UI)."""
    if not _known_users:
        raise HTTPException(status_code=503, detail="Data not loaded yet")
    # Ensure all IDs are native Python ints for JSON serialization
    users = sorted([int(uid) for uid in _known_users])[:limit]
    return {"total": len(_known_users), "users": users}


# ---------------------------------------------------------------------------
# Profile Management Endpoints
# ---------------------------------------------------------------------------

@app.put("/auth/me/genres")
async def update_user_genres_endpoint(genres: dict = None, current_user: dict = Depends(get_current_user)):
    """Update user's preferred genres."""
    if not genres or "preferred_genres" not in genres:
        raise HTTPException(status_code=400, detail="preferred_genres required")

    try:
        update_user_genres(current_user["id"], genres["preferred_genres"])
        return {"success": True, "message": "Genres updated"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------------------------
# Wishlist Endpoints
# ---------------------------------------------------------------------------

@app.post("/wishlist/{movie_id}")
async def add_to_wishlist_endpoint(movie_id: int, movie_data: dict = None, current_user: dict = Depends(get_current_user)):
    """Add movie to user's wishlist."""
    title = movie_data.get("title", "") if movie_data else ""
    genres = movie_data.get("genres", "") if movie_data else ""

    if add_to_wishlist(current_user["id"], movie_id, title, genres):
        return {"success": True, "message": "Added to wishlist"}
    raise HTTPException(status_code=400, detail="Failed to add to wishlist")


@app.delete("/wishlist/{movie_id}")
async def remove_from_wishlist_endpoint(movie_id: int, current_user: dict = Depends(get_current_user)):
    """Remove movie from user's wishlist."""
    if remove_from_wishlist(current_user["id"], movie_id):
        return {"success": True, "message": "Removed from wishlist"}
    raise HTTPException(status_code=400, detail="Failed to remove from wishlist")


@app.get("/wishlist")
async def get_wishlist_endpoint(current_user: dict = Depends(get_current_user)):
    """Get user's wishlist."""
    wishlist = get_user_wishlist(current_user["id"])
    return {
        "user_id": current_user["id"],
        "wishlist_count": len(wishlist),
        "wishlist": wishlist
    }


@app.get("/wishlist/{movie_id}/check")
async def check_in_wishlist(movie_id: int, current_user: dict = Depends(get_current_user)):
    """Check if movie is in user's wishlist."""
    return {"in_wishlist": is_in_wishlist(current_user["id"], movie_id)}


# ---------------------------------------------------------------------------
# Admin Endpoints
# ---------------------------------------------------------------------------

@app.get("/admin/users")
async def admin_list_users(limit: int = Query(default=50, ge=1, le=500), offset: int = Query(default=0, ge=0), current_user: dict = Depends(get_current_user)):
    """Admin: Get all users."""
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    users, total = get_all_users(limit, offset)
    return {"total": total, "limit": limit, "offset": offset, "users": users}


@app.delete("/admin/users/{user_id}")
async def admin_delete_user(user_id: int, current_user: dict = Depends(get_current_user)):
    """Admin: Delete a user."""
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    if user_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    if delete_user(user_id):
        return {"success": True, "message": "User deleted"}
    raise HTTPException(status_code=400, detail="Failed to delete user")


@app.put("/admin/users/{user_id}/promote")
async def admin_promote_user(user_id: int, current_user: dict = Depends(get_current_user)):
    """Admin: Promote user to admin."""
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    if promote_user_to_admin(user_id):
        return {"success": True, "message": "User promoted to admin"}
    raise HTTPException(status_code=400, detail="Failed to promote user")


@app.put("/admin/users/{user_id}/demote")
async def admin_demote_user(user_id: int, current_user: dict = Depends(get_current_user)):
    """Admin: Demote admin to regular user."""
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    if demote_admin_to_user(user_id):
        return {"success": True, "message": "Admin demoted to user"}
    raise HTTPException(status_code=400, detail="Failed to demote user")


@app.get("/admin/movies")
async def admin_list_movies(limit: int = Query(default=50, ge=1, le=500), offset: int = Query(default=0, ge=0), current_user: dict = Depends(get_current_user)):
    """Admin: Get all movies."""
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    movies, total = get_all_movies_from_db(limit, offset)
    return {"total": total, "limit": limit, "offset": offset, "movies": movies}


@app.delete("/admin/movies/{movie_id}")
async def admin_delete_movie(movie_id: int, current_user: dict = Depends(get_current_user)):
    """Admin: Delete a movie."""
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    if delete_movie(movie_id):
        return {"success": True, "message": "Movie deleted"}
    raise HTTPException(status_code=400, detail="Failed to delete movie")
