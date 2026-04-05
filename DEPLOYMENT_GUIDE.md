# StreamRec Deployment Guide - Vercel + Render

Complete step-by-step guide to deploy StreamRec to the internet for free.

---

## 📋 Prerequisites (Do These First)

### 1. Create GitHub Account (If you don't have one)
- Go to https://github.com
- Click "Sign up"
- Create account with your email
- Verify email

### 2. Push Your Code to GitHub

```bash
# Navigate to project directory
cd /Users/kcsn/projects/movie-rec-engine

# Initialize git (if not already done)
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit - StreamRec app ready for deployment"

# Create GitHub repository manually:
# 1. Go to https://github.com/new
# 2. Repository name: movie-rec-engine
# 3. Description: "Movie Recommendation Engine"
# 4. Create repository (don't add README)

# Add remote and push
git remote add origin https://github.com/YOUR_USERNAME/movie-rec-engine.git
git branch -M main
git push -u origin main
```

Replace `YOUR_USERNAME` with your actual GitHub username!

---

## 🔧 PART 1: BACKEND DEPLOYMENT ON RENDER

### Step 1: Create Render Account
1. Go to https://render.com
2. Click "Sign up"
3. Choose "Sign up with GitHub" (easier)
4. Authorize Render to access GitHub
5. Click "Create New" on dashboard

---

### Step 2: Create PostgreSQL Database on Render

**2.1: Create Database**
1. Click "New +" button
2. Select "PostgreSQL"
3. Fill in details:
   - **Name**: `streamrec-db`
   - **Database**: `streamrec`
   - **User**: `streamrec_user`
   - **Region**: Choose closest to you (e.g., Singapore for Asia)
   - **PostgreSQL Version**: 15
4. Click "Create Database"
5. ⏳ **Wait 2-3 minutes** for database to be created
6. **Copy the connection string** (looks like):
   ```
   postgresql://streamrec_user:PASSWORD@HOST:5432/streamrec
   ```
   Save it somewhere safe!

---

### Step 3: Create Backend Web Service on Render

**3.1: Create Web Service**
1. Back on Render dashboard, click "New +"
2. Select "Web Service"
3. Choose "Deploy an existing repository"
4. Click "GitHub" if not already connected
5. Search for `movie-rec-engine` repository
6. Select it and click "Connect"

**3.2: Configure Backend Service**
Fill in these fields:

| Field | Value |
|-------|-------|
| **Name** | `streamrec-api` |
| **Environment** | `Docker` |
| **Region** | Same as database (e.g., Singapore) |
| **Branch** | `main` |
| **Build Command** | Leave empty (Docker will handle) |
| **Start Command** | Leave empty (Docker will handle) |

**3.3: Add Environment Variables**
1. Scroll to "Environment" section
2. Add these variables:
   - **KEY**: `DATABASE_URL`
     **VALUE**: Paste your PostgreSQL connection string from Step 2

   - **KEY**: `PYTHONPATH`
     **VALUE**: `/app`

   - **KEY**: `MODEL_DIR`
     **VALUE**: `/app/data/processed`

   - **KEY**: `DATA_DIR`
     **VALUE**: `/app/data/raw`

**3.4: Deploy**
1. Click "Create Web Service"
2. ⏳ **Wait 5-10 minutes** for build to complete
3. Once deployed, you'll see a green "Live" status
4. **Copy your backend URL** (looks like): `https://streamrec-api.onrender.com`

**Check if backend is working:**
- Go to `https://streamrec-api.onrender.com/health`
- Should see: `{"status":"ok",...}`

---

## 🎨 PART 2: FRONTEND DEPLOYMENT ON VERCEL

### Step 1: Create Vercel Account
1. Go to https://vercel.com
2. Click "Sign Up"
3. Choose "Continue with GitHub"
4. Authorize Vercel
5. You'll be redirected to dashboard

---

### Step 2: Deploy Frontend

**2.1: Import Project**
1. Click "New Project"
2. Click "Import Git Repository"
3. Search for `movie-rec-engine`
4. Select it and click "Import"

**2.2: Configure Project**
1. **Select Root Directory**: `./frontend`
   - Click "Edit" next to "Root Directory"
   - Type: `frontend`
   - Click "Save"

2. **Environment Variables**
   - Add one variable:
     - **KEY**: `NEXT_PUBLIC_API_BASE`
     - **VALUE**: Your backend URL from Part 1 (e.g., `https://streamrec-api.onrender.com`)

**2.3: Deploy**
1. Click "Deploy"
2. ⏳ **Wait 3-5 minutes** for deployment
3. Once done, you'll see "Congratulations! Your site is live"
4. **Your frontend URL**: Copy the domain (looks like): `https://streamrec-frontend.vercel.app`

---

## ✅ TESTING & VERIFICATION

### Test 1: Check Backend Health
```
Go to: https://streamrec-api.onrender.com/health
Expected: {"status":"ok","model_loaded":true,...}
```

### Test 2: Check API Documentation
```
Go to: https://streamrec-api.onrender.com/docs
Expected: Interactive API documentation page
```

### Test 3: Visit Frontend
```
Go to: https://streamrec-frontend.vercel.app (or your URL)
Expected: Login page loads
```

### Test 4: Login Test
```
Email: admin@gmail.com
Password: admin
Expected: Redirected to admin dashboard with users list
```

---

## 🔗 CONNECTING FRONTEND TO BACKEND

⚠️ **Important**: Make sure `NEXT_PUBLIC_API_BASE` environment variable on Vercel points to your Render backend!

### How to Update if Backend URL Changes:

1. Go to Vercel dashboard
2. Select `movie-rec-engine` project
3. Go to "Settings" → "Environment Variables"
4. Click edit on `NEXT_PUBLIC_API_BASE`
5. Update with new backend URL
6. Redeploy: Go to "Deployments" → Click "Redeploy" on latest deployment

---

## 🚨 TROUBLESHOOTING

### Frontend shows "Cannot connect to API"
**Solution:**
1. Check backend URL is correct in Vercel environment variables
2. Verify backend is running: `https://your-backend-url/health`
3. Check browser console for CORS errors
4. Redeploy frontend after updating URL

### Backend shows "No users found"
**Solution:**
1. Check Render logs: Click on deployment → "Logs"
2. Look for "Seeding users" message
3. Wait 1-2 minutes for initial startup
4. Refresh page

### Database connection error
**Solution:**
1. Verify `DATABASE_URL` is correct
2. Check PostgreSQL is "Available" in Render dashboard
3. Try restarting web service: Render dashboard → Restart

### Slow loading (Render spins down after 15 min inactivity)
**Note:** Free tier spins down. First visit after inactive time = slow load (30-60 sec)
**Solution:** Upgrade to paid tier if needed, or just wait for first load

---

## 📊 FREE TIER LIMITATIONS

| Resource | Limit | Details |
|----------|-------|---------|
| **Backend (Web Service)** | Spins down after 15 min | Cold starts ~30 sec |
| **Database** | 256MB | Should be enough for demo |
| **Bandwidth** | Limited | Should be fine for testing |
| **Frontend** | Unlimited | Vercel's free tier is generous |

---

## 💰 PRICING REFERENCE

If you want to remove cold starts:

**Render:**
- Basic ($7/month): No spin-down, 0.5GB RAM
- PostgreSQL: $15/month for 1GB

**Vercel:**
- Free: Unlimited for frontend
- Pro ($20/month): For advanced features

**Total for production:** ~$22-40/month

---

## 🎯 FINAL CHECKLIST

- [ ] GitHub repository created and code pushed
- [ ] PostgreSQL database created on Render
- [ ] Backend deployed on Render
- [ ] Backend health check working (`/health` endpoint)
- [ ] Frontend deployed on Vercel
- [ ] `NEXT_PUBLIC_API_BASE` set correctly in Vercel
- [ ] Frontend loads at Vercel URL
- [ ] Can login with admin@gmail.com / admin
- [ ] Can see users in admin dashboard
- [ ] Wishlist feature works
- [ ] Profile settings work

---

## 🆘 GETTING HELP

**Check logs:**

**Render Backend Logs:**
1. Go to https://dashboard.render.com
2. Click on `streamrec-api` service
3. Click "Logs" tab
4. Scroll for error messages

**Vercel Frontend Logs:**
1. Go to https://vercel.com/dashboard
2. Click on `movie-rec-engine` project
3. Click "Deployments"
4. Click on latest deployment
5. Click "Logs" tab

---

## 📝 IMPORTANT NOTES

1. **Cold Starts**: First request after 15 min idle will be slow (30-60 sec)
2. **Data Persistence**: Database data persists, frontend/backend redeploys lose runtime data
3. **Environment Variables**: Changes require redeploy
4. **CORS**: If you see CORS errors, it's usually a backend URL mismatch

---

Good luck! 🚀
