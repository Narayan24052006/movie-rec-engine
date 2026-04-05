# 🎬 StreamRec - Hybrid Movie Recommendation Engine

A production-ready, full-stack movie recommendation system combining **Collaborative Filtering**, **Content-Based Filtering**, and **Cold-Start Handling** with a modern admin dashboard.

**Live Demo:** https://movie-rec-engine-1.onrender.com

---

## 🌟 What Makes StreamRec Unique?

### 1. **Hybrid Recommendation Approach**
Most recommendation engines use only one method. StreamRec intelligently blends:
- **Collaborative Filtering (70%)** - Learn from user behavior patterns
- **Content-Based Filtering (20%)** - Match movie genres and descriptions
- **Popularity Scoring (5%)** - Surface trending movies
- **Recency Weighting (5%)** - Prioritize recent releases

This multi-method approach gives **more accurate, diverse, and fresh recommendations** than single-algorithm solutions.

### 2. **Intelligent Cold-Start Handling**
New users are a problem in recommendation systems (no history = no recommendations).

StreamRec solves this:
- **Quiz-based onboarding** - Ask new users their genre preferences
- **Genre-targeted recommendations** - Start with movies matching their interests
- **Seamless transition** - Automatically switch to collaborative filtering once user has history

### 3. **Production-Ready Admin Dashboard**
Unlike most personal projects, StreamRec includes:
- **User management** - Promote/demote/delete users
- **Admin controls** - Manage entire user base
- **Clean, dark-themed UI** - Netflix-style interface
- **Role-based access** - Admin vs regular user flows

### 4. **Full-Stack Implementation**
Most ML recommendation projects lack UI. StreamRec provides:
- **FastAPI backend** - Sub-100ms response times with async/await
- **Next.js frontend** - Modern, responsive React application
- **PostgreSQL database** - Persistent storage for users and preferences
- **Authentication** - JWT-based secure login

### 5. **Easy Deployment**
Deployed on **Render free tier** without Docker:
- Auto-scales models on first startup
- Downloads MovieLens dataset automatically
- Trains recommendation models on deployment
- Models persist across restarts
- **Cost: $0/month**

### 6. **Explainable Recommendations**
Users see **not just recommendations, but WHY**:
- Which algorithm contributed (CF, Content-Based, Popularity)
- Confidence scores for each recommendation
- Similarity reasoning for "Similar Movies" feature

---

## 🎯 Key Features

✅ **Hybrid Recommendations** - Collaborative + Content-Based + Popularity + Recency
✅ **Cold-Start Handling** - Quiz-based recommendations for new users
✅ **User Authentication** - Secure JWT-based login with Gmail validation
✅ **Admin Dashboard** - Manage users, promote admins, delete accounts
✅ **Wishlist System** - Save movies for later
✅ **Similar Movies** - Find movies related to your favorites
✅ **Personalization** - Genre preferences and watch history
✅ **Real-time** - Fast API response times (<100ms)
✅ **Explainability** - See why each movie was recommended
✅ **Production Ready** - Deployed and live on internet

---

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern, fast web framework
- **PostgreSQL** - Relational database
- **Scikit-learn** - ML algorithms (ALS, TF-IDF)
- **Pandas & NumPy** - Data processing
- **SQLAlchemy** - ORM for database access
- **Uvicorn** - ASGI server

### Frontend
- **Next.js 16** - React framework with SSR
- **React 19** - UI library
- **TailwindCSS** - Styling
- **Axios** - HTTP client

### ML Models
- **Funk-SVD (Collaborative Filtering)** - Matrix factorization with 128 factors
- **TF-IDF (Content-Based)** - Genre + title similarity (5,528 features)
- **Popularity Score** - Average ratings × vote count
- **Recency Weighting** - Recent movies boost

### Dataset
- **MovieLens Small** - 100K+ ratings, 9,700+ movies, 600+ users
- **Auto-downloaded** on first startup

---

## 📊 How It Works

### Recommendation Flow

```
User Login
    ↓
Check if Known User (in dataset)
    ├─→ YES: Use Collaborative Filtering (ALS Model)
    │        └─→ Blend with Content-Based + Popularity
    │        └─→ Return top-N with scores
    │
    └─→ NO (Cold-Start)
         ├─→ Has Genre Preferences?
         │   ├─→ YES: Content-Based on genres
         │   └─→ NO: Popular movies fallback
         └─→ Store preferences in DB
              └─→ Transition to CF on next visit
```

### Model Training

On first deployment, StreamRec:
1. Downloads MovieLens dataset (~10MB)
2. Preprocesses ratings (stratified train/val/test split)
3. Trains Collaborative Filtering model (30 epochs, RMSE ~0.79)
4. Trains Content-Based model (5,528 TF-IDF features)
5. Persists models to disk (reused on restarts)

**Total training time:** ~2-3 minutes (one-time)

---

## 🚀 Live Deployment

### URLs
```
Frontend:  https://movie-rec-engine-1.onrender.com
Backend:   https://movie-rec-engine-pheb.onrender.com
API Docs:  https://movie-rec-engine-pheb.onrender.com/docs
```

### Test Credentials
```
Admin Login:
  Email: admin@gmail.com
  Password: admin

Regular User (from MovieLens):
  Email: user_1@gmail.com
  Password: (any password)
```

### API Endpoints

```bash
# Get recommendations for user
GET /recommendations/{user_id}?top_n=20

# Find similar movies
GET /similar-items/{movie_id}?top_n=20

# Explain a recommendation
GET /explain/{user_id}/{item_id}

# Submit quiz for cold-start users
POST /quiz
{
  "preferred_genres": ["Action", "Sci-Fi"],
  "top_n": 10
}

# Authentication
POST /auth/login
POST /auth/register
GET /auth/me

# Admin features
GET /admin/users?limit=50&offset=0
PUT /admin/users/{user_id}/promote
DELETE /admin/users/{user_id}

# Health check
GET /health
```

---

## 💻 Local Development

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL 14+

### Backend Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://user:password@localhost/streamrec"
export DATA_DIR="data/raw"
export MODEL_DIR="data/processed"

# Run API
uvicorn src.api.main:app --reload
```

Backend runs on `http://localhost:8000`

### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Set backend URL
export NEXT_PUBLIC_API_BASE="http://localhost:8000"

# Run dev server
npm run dev
```

Frontend runs on `http://localhost:3000`

---

## 📈 Performance Metrics

| Metric | Value |
|--------|-------|
| Recommendation Latency | <100ms |
| Model Training Time | ~2-3 min |
| Dataset Size | 100K+ ratings |
| Unique Movies | 9,742 |
| Unique Users | 610+ |
| CF Model RMSE | 0.7959 |
| CBF Features | 5,528 |
| Admin Users | Configurable |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│           Next.js Frontend (Render)             │
│  - Login/Register                               │
│  - Admin Dashboard (User Management)            │
│  - Recommendations Display                      │
│  - Wishlist Feature                             │
└────────────────────┬────────────────────────────┘
                     │ JWT Auth + REST API
                     ↓
┌─────────────────────────────────────────────────┐
│          FastAPI Backend (Render)               │
│  ├─ Auth Endpoints                              │
│  ├─ Recommendation Engine                       │
│  │  ├─ Collaborative Filtering (ALS)           │
│  │  ├─ Content-Based Filtering (TF-IDF)        │
│  │  ├─ Cold-Start Handler                      │
│  │  └─ Hybrid Blender                          │
│  ├─ Admin Endpoints                             │
│  └─ Health Check                                │
└────────────────────┬────────────────────────────┘
                     │ SQLAlchemy ORM
                     ↓
┌─────────────────────────────────────────────────┐
│      PostgreSQL Database (Render)               │
│  - Users (auth, preferences, admin status)     │
│  - Ratings (user → movie feedback)             │
│  - Movies (catalog)                            │
│  - Tags (genre metadata)                       │
│  - Wishlist (saved movies)                     │
└─────────────────────────────────────────────────┘
                     ↑
            [MovieLens Dataset]
            (Auto-downloaded on deploy)
```

---

## 🔄 Comparison with Other Solutions

| Feature | StreamRec | Netflix | Content-Only Services |
|---------|-----------|---------|----------------------|
| Hybrid Recommendations | ✅ | ✅ | ❌ |
| Cold-Start Handling | ✅ | ✅ | ❌ |
| Admin Dashboard | ✅ | (Internal) | ❌ |
| Explainability | ✅ | Partial | ❌ |
| Open Source | ✅ | ❌ | Varies |
| Free Deployment | ✅ | ❌ | Varies |
| Full-Stack | ✅ | ✅ | Partial |
| ML Interpretable | ✅ | ❌ | Varies |

---

## 📝 License

MIT License - Feel free to use, modify, and distribute

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Deep Learning models (Neural Collaborative Filtering)
- Real-time personalization
- Movie clustering visualization
- A/B testing framework
- Performance optimizations

---

## 📧 Contact & Support

For questions or issues:
- Check `/docs` endpoint for API documentation
- Review logs in Render dashboard
- Open an issue on GitHub

---

## 🎓 Learning Resources

Built with:
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [Next.js Guide](https://nextjs.org/learn)
- [Scikit-learn ML Models](https://scikit-learn.org)
- [MovieLens Dataset](https://grouplens.org/datasets/movielens/)

---

**StreamRec** - Where recommendations meet intelligence. 🎬✨
