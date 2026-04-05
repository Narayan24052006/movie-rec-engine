# 🚀 STREAMREC DEPLOYMENT - QUICK REFERENCE CARD

## 📱 KEEP THIS HANDY!

---

## 💻 COMMANDS TO RUN

```bash
# Step 1: Push code to GitHub
cd /Users/kcsn/projects/movie-rec-engine
git remote add origin https://github.com/YOUR_USERNAME/movie-rec-engine.git
git branch -M main
git push -u origin main

# Step 2: Test backend URL
curl https://YOUR_BACKEND_URL/health

# Step 3: Visit frontend
https://YOUR_FRONTEND_URL
```

---

## 🔗 YOUR DEPLOYMENT URLS

**Save these once you deploy:**

```
Frontend:   https://__________________________.vercel.app
Backend:    https://__________________________.onrender.com
API Docs:   https://__________________________.onrender.com/docs
Health:     https://__________________________.onrender.com/health
```

---

## 🔑 LOGIN CREDENTIALS

```
Admin Email:    admin@gmail.com
Admin Password: admin

Test User:      user_1@gmail.com
Test Password:  password123
```

---

## ⏱️ TIMING

| Task | Duration | Notes |
|------|----------|-------|
| GitHub Setup | 5 min | Quick |
| PostgreSQL DB | 5 min | 2-3 min to create |
| Backend Deploy | 10 min | 5-10 min to build |
| Frontend Deploy | 8 min | 3-5 min to build |
| Testing | 5 min | Make sure it works |
| **TOTAL** | **35 min** | From zero to live! |

---

## 🎯 DEPLOYMENT ORDER

```
1. GitHub (push code)
   ↓
2. Render PostgreSQL (create database)
   ⏳ WAIT 2-3 MIN
   ↓
3. Render Backend (deploy with DB_URL)
   ⏳ WAIT 5-10 MIN ← Copy backend URL when done
   ↓
4. Vercel Frontend (deploy with NEXT_PUBLIC_API_BASE)
   ⏳ WAIT 3-5 MIN ← Copy frontend URL when done
   ↓
5. TEST (verify everything works)
```

---

## 🔐 ENVIRONMENT VARIABLES

### Render Backend
```
DATABASE_URL = postgresql://streamrec_user:...@...
PYTHONPATH = /app
MODEL_DIR = /app/data/processed
DATA_DIR = /app/data/raw
```

### Vercel Frontend
```
NEXT_PUBLIC_API_BASE = https://streamrec-api.onrender.com
(use YOUR actual backend URL)
```

---

## ✅ QUICK TEST CHECKLIST

- [ ] Backend health check: `/health` returns JSON
- [ ] Frontend loads: See login page
- [ ] Admin login: Can login with admin@gmail.com
- [ ] See users: Admin dashboard shows 1225 users
- [ ] Functionality: Can promote/demote/delete users

---

## 🆘 QUICK FIXES

| Problem | Solution |
|---------|----------|
| Can't connect | Check NEXT_PUBLIC_API_BASE on Vercel |
| Login fails | Wait 2 min, try different browser |
| No users show | Wait 5 min, refresh page |
| 502 error | Wait 60 sec (cold start), try again |
| Build fails | Check Render/Vercel logs |

---

## 📊 EXPECTED PERFORMANCE

**First load (cold start):** 30-60 seconds
**Subsequent loads:** 1-2 seconds
**Admin dashboard:** <1 second per action
**Database queries:** 100-200ms

*(Free tier spins down after 15 min inactivity)*

---

## 💡 PRO TIPS

✅ Go to bed after clicking "Deploy" - it finishes itself
✅ Check logs if something seems wrong
✅ Frontend changes auto-deploy when you push
✅ Backend changes auto-deploy when you push
✅ Save your URLs immediately after deploy
✅ Share frontend URL with users - they don't need backend URL!

---

## 📞 HELP

**Render Dashboard**: https://dashboard.render.com
**Vercel Dashboard**: https://vercel.com/dashboard
**Status Pages**: render.com/status, vercelstatus.com

---

**Status**: Not yet deployed ☐ | Deploying 🔄 | Deployed ✅

