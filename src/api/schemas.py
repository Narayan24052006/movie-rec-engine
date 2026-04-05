"""
Pydantic Schemas for API Validation
=====================================
Strongly-typed request/response models to prevent runtime errors.
All numeric IDs are cast to native Python int to avoid numpy.int32
JSON serialization failures.
"""

from typing import Dict, List, Optional
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class UserQuizRequest(BaseModel):
    """Request body for the cold-start user quiz."""
    preferred_genres: List[str] = Field(
        ...,
        description="List of genre strings the new user selected",
        examples=[["Sci-Fi", "Thriller", "Drama"]],
    )
    top_n: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Number of recommendations to return",
    )


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class RecommendationItem(BaseModel):
    """A single recommendation entry."""
    movieId: int = 0
    title: str = ""
    genres: str = ""
    score: float = 0.0
    cf_score: float = 0.0
    cbf_score: float = 0.0
    pop_score: float = 0.0
    rec_score: float = 0.0
    source: str = "hybrid"

    @field_validator("movieId", mode="before")
    @classmethod
    def cast_movie_id(cls, v):
        return int(v)

    @field_validator("score", "cf_score", "cbf_score", "pop_score", "rec_score", mode="before")
    @classmethod
    def cast_float(cls, v):
        return float(v) if v is not None else 0.0


class RecommendationResponse(BaseModel):
    """Top-N recommendations for a user."""
    user_id: int
    recommendations: List[RecommendationItem]
    is_cold_start: bool = False
    total: int = 0

    @field_validator("user_id", mode="before")
    @classmethod
    def cast_user_id(cls, v):
        return int(v)


class SimilarItemResponse(BaseModel):
    """Similar items for a given movie."""
    movie_id: int
    title: str = ""
    similar_items: List[RecommendationItem]

    @field_validator("movie_id", mode="before")
    @classmethod
    def cast_movie_id(cls, v):
        return int(v)


class ExplanationResponse(BaseModel):
    """Explanation for why a movie was recommended."""
    user_id: int
    movie_id: int
    cf_score: float = 0.0
    cbf_score: float = 0.0
    popularity: float = 0.0
    avg_rating: float = 0.0
    genres: List[str] = []
    most_similar_liked_item: Optional[int] = None
    similarity_to_liked: float = 0.0
    top_matching_features: Dict[str, float] = {}
    explanation_text: str = ""

    @field_validator("user_id", "movie_id", mode="before")
    @classmethod
    def cast_ids(cls, v):
        return int(v) if v is not None else 0

    @field_validator("most_similar_liked_item", mode="before")
    @classmethod
    def cast_optional_id(cls, v):
        return int(v) if v is not None else None

    @field_validator("popularity", "avg_rating", "cf_score", "cbf_score",
                     "similarity_to_liked", mode="before")
    @classmethod
    def cast_floats(cls, v):
        return float(v) if v is not None else 0.0


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "ok"
    model_loaded: bool = False
    n_users: int = 0
    n_items: int = 0


# ---------------------------------------------------------------------------
# Auth Models
# ---------------------------------------------------------------------------

class UserRegisterRequest(BaseModel):
    username: str
    password: str
    preferred_genres: List[str] = []

class UserLoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    
class UserProfileResponse(BaseModel):
    id: int
    username: str
    preferred_genres: List[str]
    is_admin: bool
    created_at: datetime
