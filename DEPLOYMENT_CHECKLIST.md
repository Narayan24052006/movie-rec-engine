# ✅ STREAMREC DEPLOYMENT CHECKLIST

**Your Name**: ________________
**Date Started**: ________________
**Target Launch Date**: ________________

---

## 📋 PRE-DEPLOYMENT (Do Once)

### GitHub Preparation
- [ ] Create GitHub account (if needed) → https://github.com/signup
- [ ] Navigate to project: `cd /Users/kcsn/projects/movie-rec-engine`
- [ ] Create new GitHub repository → https://github.com/new
- [ ] Name it: `movie-rec-engine`
- [ ] Copy your GitHub username: `_____________________`
- [ ] Add remote: `git remote add origin https://github.com/YOUR_USERNAME/movie-rec-engine.git`
- [ ] Push code: `git branch -M main && git push -u origin main`
- [ ] Verify on GitHub: Visit https://github.com/YOUR_USERNAME/movie-rec-engine

---

## 🗄️ PHASE 1: RENDER (Backend + Database)

### A. Create Render Account
- [ ] Go to https://render.com
- [ ] Sign up with GitHub
- [ ] Connect GitHub account
- [ ] Verify email (check spam folder!)
- [ ] Land on Render dashboard

**Save your Render account info:**
```
Email: _____________________
Password: _____________________ (if needed later)
```

### B. Deploy PostgreSQL Database

⏱️ **Estimated time: 5 minutes (mostly waiting)**

1. [ ] Click "New +" button on Render dashboard
2. [ ] Select "PostgreSQL"
3. [ ] Fill in database form:
   - [ ] Name: `streamrec-db`
   - [ ] Database name: `streamrec`
   - [ ] User: `streamrec_user`
   - [ ] Password: (auto-generated, that's OK)
   - [ ] Region: Choose one close to you (e.g., Singapore)
   - [ ] PostgreSQL Version: `15`

4. [ ] Click "Create Database"
5. [ ] ⏳ **WAIT 2-3 MINUTES**
6. [ ] Status should change to "Available"
7. [ ] Click on database name
8. [ ] Find "Connections" section
9. [ ] **COPY** the connection string (starts with `postgresql://`)
10. [ ] Save it here:
```
DATABASE_URL:
_________________________________________________
_________________________________________________
```

### C. Deploy Backend (FastAPI)

⏱️ **Estimated time: 10 minutes (mostly building)**

1. [ ] Back to Render dashboard
2. [ ] Click "New +" button
3. [ ] Select "Web Service"
4. [ ] Choose "Deploy an existing repository"
5. [ ] Click "GitHub" (connect if needed)
6. [ ] Search and select: `movie-rec-engine`
7. [ ] Click "Connect"

**Configure Service:**
8. [ ] Name: `streamrec-api`
9. [ ] Environment: `Docker`
10. [ ] Region: **SAME AS DATABASE** (important!)
11. [ ] Branch: `main`
12. [ ] Leave Build Command empty
13. [ ] Leave Start Command empty

**Add Environment Variables:**
14. [ ] Scroll to "Environment" section
15. [ ] Add 4 variables:

Variables to add:
```
1. DATABASE_URL = [paste from above]
2. PYTHONPATH = /app
3. MODEL_DIR = /app/data/processed
4. DATA_DIR = /app/data/raw
```

- [ ] Click "Add Environment Variable" for each one
- [ ] Paste DATABASE_URL value
- [ ] Enter PYTHONPATH value: `/app`
- [ ] Enter MODEL_DIR value: `/app/data/processed`
- [ ] Enter DATA_DIR value: `/app/data/raw`

16. [ ] Click "Create Web Service"
17. [ ] ⏳ **WAIT 5-10 MINUTES** - you'll see build logs
18. [ ] Status should turn **GREEN**
19. [ ] Copy your backend URL:

```
Backend URL: https://streamrec-api.onrender.com
(or whatever Render gave you)
Replace above with YOUR actual URL:
https://______________________________
```

**Test Backend:**
20. [ ] Open browser to: `https://YOUR_BACKEND_URL/health`
21. [ ] Should see: `{"status":"ok",...}`
22. [ ] If not, check Render logs (something went wrong)

---

## 🎨 PHASE 2: VERCEL (Frontend)

### A. Create Vercel Account
- [ ] Go to https://vercel.com
- [ ] Click "Sign Up"
- [ ] Choose "Continue with GitHub"
- [ ] Authorize Vercel
- [ ] Land on Vercel dashboard

**Save your Vercel account info:**
```
Email: _____________________
```

### B. Deploy Frontend (Next.js)

⏱️ **Estimated time: 8 minutes (mostly building)**

1. [ ] Click "New Project"
2. [ ] Click "Import Git Repository"
3. [ ] Search: `movie-rec-engine`
4. [ ] Select it and click "Import"

**Configure Project:**
5. [ ] Look for "Root Directory" setting
6. [ ] Click "Edit" next to it
7. [ ] Type: `frontend` (very important!)
8. [ ] Click "Save"

**Add Environment Variable:**
9. [ ] Scroll to "Environment Variables"
10. [ ] Click "Add New"
11. [ ] KEY: `NEXT_PUBLIC_API_BASE`
12. [ ] VALUE: **Paste your backend URL from Phase 1**
    ```
    https://streamrec-api.onrender.com
    (use YOUR actual URL)
    ```
13. [ ] Click "Save"

**Deploy:**
14. [ ] Click "Deploy"
15. [ ] ⏳ **WAIT 3-5 MINUTES**
16. [ ] See "Congratulations! Your site is live" ✅
17. [ ] Copy your frontend URL:

```
Frontend URL: https://streamrec-frontend.vercel.app
(or whatever Vercel gave you)
Replace above with YOUR actual URL:
https://______________________________
```

**Test Frontend:**
18. [ ] Open your frontend URL in browser
19. [ ] Should see: Login page
20. [ ] If not, check Vercel logs

---

## ✅ PHASE 3: TESTING (Critical!)

### Test 1: Backend Health
- [ ] URL: `https://YOUR_BACKEND_URL/health`
- [ ] Result: `{"status":"ok",...}`
- [ ] Status: ✅ PASS / ❌ FAIL

### Test 2: Frontend Loads
- [ ] URL: `https://YOUR_FRONTEND_URL`
- [ ] See: Login page with form
- [ ] Status: ✅ PASS / ❌ FAIL

### Test 3: Admin Login
Steps:
1. [ ] Open frontend URL
2. [ ] Email: `admin@gmail.com`
3. [ ] Password: `admin`
4. [ ] Click "Sign In"
5. [ ] See: Admin dashboard loading
6. [ ] See: Users table with 1225 users
7. [ ] Status: ✅ PASS / ❌ FAIL

### Test 4: User Management
- [ ] Can see users in table: ✅ YES / ❌ NO
- [ ] Pagination works (click Next): ✅ YES / ❌ NO
- [ ] Can promote user: ✅ YES / ❌ NO
- [ ] Can demote admin: ✅ YES / ❌ NO
- [ ] Can delete user: ✅ YES / ❌ NO
- [ ] Success messages appear: ✅ YES / ❌ NO

### Test 5: Regular User Features
- [ ] Register new user: ✅ PASS / ❌ FAIL
- [ ] Can see "For You" recommendations: ✅ YES / ❌ NO
- [ ] Can see "Similar Movies": ✅ YES / ❌ NO
- [ ] Can add to wishlist: ✅ YES / ❌ NO
- [ ] Can view wishlist: ✅ YES / ❌ NO
- [ ] Profile settings work: ✅ YES / ❌ NO

---

## 🎉 FINAL SETUP

### Save Your Live URLs
```
✅ FRONTEND (Share this with users!)
https://________________________________

✅ BACKEND (For reference)
https://________________________________

✅ API DOCUMENTATION
https://________________________________/docs

✅ HEALTH CHECK
https://________________________________/health
```

### Share Your App!
- [ ] Copy frontend URL
- [ ] Send to friends/family
- [ ] They can now use your app!
- [ ] Tell them default admin login:
  - Email: admin@gmail.com
  - Password: admin

---

## 📊 MONITORING CHECKLIST (Do Weekly)

- [ ] Check Render backend status
- [ ] Check Vercel deployment status
- [ ] Test login works
- [ ] Check no error messages
- [ ] Review logs for issues

---

## 🔄 UPDATE CHECKLIST (When You Make Changes)

To deploy updates:

1. [ ] Make code changes locally
2. [ ] Test: `docker compose up`
3. [ ] Commit: `git add . && git commit -m "..."`
4. [ ] Push: `git push origin main`
5. [ ] Render auto-rebuilds (watch logs)
6. [ ] Vercel auto-rebuilds (watch dashboard)
7. [ ] Test live site again

---

## 🆘 TROUBLESHOOTING NOTES

**If something breaks, check here:**

Issue: Can't connect to API
- [ ] Check backend URL is correct on Vercel
- [ ] Check backend is running (green status on Render)
- [ ] Check health endpoint works

Issue: Login doesn't work
- [ ] Wait 2 minutes after first deploy
- [ ] Check browser console for errors
- [ ] Try incognito mode (clear cache)

Issue: No users showing
- [ ] Wait 5 minutes for database to initialize
- [ ] Check Render logs for "Seeding users"
- [ ] Refresh page

Issue: 502 Gateway Error
- [ ] Backend crashed - check Render logs
- [ ] Wait for cold start (might take 60 sec)
- [ ] Try visiting again in 1 minute

---

## 📞 HELP LINKS

Render Support: https://render.com/support
Vercel Support: https://vercel.com/support
FastAPI Docs: https://fastapi.tiangolo.com
Next.js Docs: https://nextjs.org/docs

---

## 📝 NOTES & OBSERVATIONS

```
Date: ________________
Notes:
_________________________________________________
_________________________________________________
_________________________________________________

Issues encountered:
_________________________________________________
_________________________________________________

Solutions found:
_________________________________________________
_________________________________________________

Performance observations:
_________________________________________________
_________________________________________________
```

---

## ✨ COMPLETION STATUS

- [ ] All tests passing
- [ ] App live on internet
- [ ] Can login and use
- [ ] Admin dashboard working
- [ ] Regular features working
- [ ] Ready for users!

**Status**: ✅ READY FOR LAUNCH!

---

**Deployment Completed By**: ____________________
**Completion Date**: ____________________
**Time Taken**: ____ hours

Congratulations! Your StreamRec app is now live! 🚀

