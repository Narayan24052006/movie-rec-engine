# 🚀 QUICK DEPLOYMENT CHECKLIST

## BEFORE YOU START
```bash
# Make sure everything is committed to GitHub
cd /Users/kcsn/projects/movie-rec-engine
git status  # Should show "nothing to commit"
git log     # Should show your commits
```

---

## ⏱️ ESTIMATED TIME: 20-30 minutes

---

## 🔄 STEP-BY-STEP (COPY-PASTE READY)

### PHASE 1: SETUP (5 minutes)

**1. Create GitHub Repo**
```
Go to: https://github.com/new
Name: movie-rec-engine
Create it (choose Public or Private)
```

**2. Push Your Code**
```bash
cd /Users/kcsn/projects/movie-rec-engine
git remote add origin https://github.com/YOUR_USERNAME/movie-rec-engine.git
git branch -M main
git push -u origin main

# Verify it worked:
# Go to https://github.com/YOUR_USERNAME/movie-rec-engine
# Should see all your files
```

---

### PHASE 2: DEPLOY BACKEND (10 minutes)

**Step A: Create Database**
```
1. Go to https://render.com
2. Sign up with GitHub
3. Click "New +" → "PostgreSQL"
4. Name: streamrec-db
5. Database: streamrec
6. User: streamrec_user
7. Region: Choose closest to you
8. Click "Create Database"
9. WAIT 2-3 MINUTES ⏳
10. Copy connection string (save it!)
```

**Step B: Deploy API**
```
1. Back on Render dashboard
2. Click "New +" → "Web Service"
3. Select your GitHub repo
4. Name: streamrec-api
5. Environment: Docker
6. Region: SAME as database
7. Add Environment Variables:
   - DATABASE_URL = [paste connection string]
   - PYTHONPATH = /app
   - MODEL_DIR = /app/data/processed
   - DATA_DIR = /app/data/raw
8. Click "Create Web Service"
9. WAIT 5-10 MINUTES ⏳
10. Check status turns GREEN ✅
11. COPY YOUR BACKEND URL (e.g., https://streamrec-api.onrender.com)
```

**Verify Backend Works:**
```
Go to: https://streamrec-api.onrender.com/health
Should see: {"status":"ok",...}
```

---

### PHASE 3: DEPLOY FRONTEND (8 minutes)

**Step A: Deploy to Vercel**
```
1. Go to https://vercel.com
2. Sign up with GitHub
3. Click "New Project"
4. Import Git Repository
5. Select your repo
6. Root Directory: ./frontend (IMPORTANT!)
7. Add Environment Variable:
   - NEXT_PUBLIC_API_BASE = https://streamrec-api.onrender.com
                            (use YOUR backend URL from above)
8. Click "Deploy"
9. WAIT 3-5 MINUTES ⏳
10. Copy your frontend URL (e.g., https://streamrec-frontend.vercel.app)
```

**Verify Frontend Works:**
```
Go to: https://streamrec-frontend.vercel.app (or your URL)
Should see: Login page
```

---

## ✅ FINAL TEST

```bash
# Test 1: Backend health
curl https://streamrec-api.onrender.com/health

# Test 2: Login
1. Open: https://streamrec-frontend.vercel.app
2. Email: admin@gmail.com
3. Password: admin
4. Should see: Admin dashboard with users

# Test 3: User management
1. Click on a user
2. Try: Promote / Demote / Delete
3. Test pagination (Next / Previous)
4. Should work smoothly ✅
```

---

## 🔐 IMPORTANT THINGS TO REMEMBER

1. **GitHub Username**: Replace with YOUR actual username
2. **Backend URL**: Copy it exactly from Render
3. **Environment Variable**: `NEXT_PUBLIC_API_BASE` must match backend URL
4. **Wait Times**: Don't skip waiting - builds take time!
5. **Cold Starts**: First request might be slow (30-60 sec)

---

## 🆘 IF SOMETHING GOES WRONG

### Login doesn't work?
- Check backend health: `BACKEND_URL/health`
- Check Render logs (look for errors)
- Restart backend service on Render

### Can't see users in admin?
- Wait 1-2 minutes for database to initialize
- Check backend logs in Render
- Refresh page

### Frontend shows "Cannot connect to API"?
- Check `NEXT_PUBLIC_API_BASE` on Vercel is correct
- Check backend URL works in browser
- Redeploy frontend on Vercel

### Database error?
- Check DatabaseURL in Render environment
- Verify PostgreSQL is "Available" status
- Restart web service

---

## 📊 YOUR LIVE URLS

After deployment, save these:

```
Frontend: https://streamrec-frontend.vercel.app
Backend:  https://streamrec-api.onrender.com
API Docs: https://streamrec-api.onrender.com/docs
```

---

## 🎉 DONE!

Your app is now live on the internet!

Share the **frontend URL** with anyone to use your app! 🚀

---

## 💡 NEXT STEPS (Optional)

- Monitor logs occasionally for errors
- Consider upgrading to paid tier if you want:
  - No cold starts
  - Better performance
  - More database space
- Add custom domain later
- Set up monitoring/alerts

