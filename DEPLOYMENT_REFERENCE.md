# 📋 DEPLOYMENT ARCHITECTURE & INFO SHEET

## 🏗️ How It All Works Together

```
┌─────────────────────────────────────────────────────────────────┐
│                         INTERNET USERS                          │
│  (anyone with the Vercel URL can access your app)               │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
        ┌────────────────────────────────┐
        │  VERCEL (Frontend)             │
        │  https://streamrec-...         │
        │  - Next.js Application         │
        │  - Beautiful UI                │
        │  - Handles user interaction    │
        └────────────────────────────────┘
                         │
         ────────────────┼────────────────
         │                              │
         ↓                              ↓
    ┌─────────┐                  ┌──────────┐
    │ Browser │────API calls────→│ RENDER   │
    │ Storage │←────JSON data────│ Backend  │
    └─────────┘                  │ (FastAPI)│
                                 │ Port 8000│
                                 └──────────┘
                                      │
                                      ↓
                            ┌──────────────────┐
                            │ PostgreSQL (DB)  │
                            │ Render           │
                            │ 256MB Free       │
                            │ Stores all data  │
                            └──────────────────┘
```

---

## 📍 URLS AFTER DEPLOYMENT

```yaml
Frontend URL:    https://streamrec-frontend.vercel.app
Backend URL:     https://streamrec-api.onrender.com
API Docs:        https://streamrec-api.onrender.com/docs
Health Check:    https://streamrec-api.onrender.com/health
```

---

## 🔑 KEY CREDENTIALS

```yaml
Admin Email:     admin@gmail.com
Admin Password:  admin

Test User:       user_1@gmail.com
Test Password:   password123
                 (or any seeded user_N@gmail.com)
```

---

## 📦 ENVIRONMENT VARIABLES REFERENCE

### On RENDER (Backend)

| Variable | Value | Example |
|----------|-------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `PYTHONPATH` | Python path | `/app` |
| `MODEL_DIR` | Model storage path | `/app/data/processed` |
| `DATA_DIR` | Raw data path | `/app/data/raw` |

### On VERCEL (Frontend)

| Variable | Value | Example |
|----------|-------|---------|
| `NEXT_PUBLIC_API_BASE` | Backend URL | `https://streamrec-api.onrender.com` |

---

## 🔀 DATA FLOW EXAMPLES

### Example 1: User Logs In
```
1. User enters email: admin@gmail.com, password: admin
2. Frontend sends: POST /auth/login to backend
3. Backend checks database (PostgreSQL)
4. Returns JWT token
5. Frontend saves token in localStorage
6. Frontend redirected to /home
```

### Example 2: Admin Views Users
```
1. Admin clicks "Admin Dashboard"
2. Frontend checks token is valid
3. Frontend calls: GET /admin/users?limit=50&offset=0
4. Backend queries PostgreSQL
5. Returns: { total: 1225, users: [...] }
6. Frontend displays users in table
```

### Example 3: Admin Deletes User
```
1. Admin clicks delete on user ID 5
2. Frontend shows confirmation
3. Frontend sends: DELETE /admin/users/5
4. Backend deletes from PostgreSQL
5. Frontend refreshes list
```

---

## ⏱️ RESPONSE TIME EXPECTATIONS

### First Load (Cold Start)
```
- Frontend: ~5 seconds (Vercel instant, but may load static assets)
- Backend: ~30-60 seconds (Render free tier spins up)
- Database: ~2 seconds (Render PostgreSQL)
```

### Subsequent Loads (Warm)
```
- Frontend: ~1-2 seconds
- Backend: ~200-500ms
- Database: ~100-200ms
- Total: ~1 second
```

---

## 📊 FREE TIER RESOURCE LIMITS

### Vercel (Frontend)
```
✅ Requests: Unlimited
✅ Bandwidth: Generous
✅ Deployments: Unlimited
✅ Functions: Yes
⚠️ Cold starts: ~1-2 sec
```

### Render (Backend)
```
⚠️ Requests: Unlimited but spins down
⚠️ Inactivity: Spins down after 15 min
⚠️ Cold start: ~30-60 sec after spin-down
✅ Deploy: Free
✅ Auto-deploy: Yes
```

### Render PostgreSQL
```
⚠️ Storage: 256MB
⚠️ No backups
✅ Auto-created with service
✅ SSL connections
```

---

## 🔄 TYPICAL WORKFLOW

```
1. Development (Local)
   ├─ Run: docker compose up
   ├─ Test: http://localhost:3000
   └─ Make changes

2. Prepare for Deployment
   ├─ Commit changes: git add . && git commit
   ├─ Push to GitHub: git push origin main
   └─ Verify on GitHub

3. Deploy Backend
   ├─ Create PostgreSQL on Render
   ├─ Create Web Service on Render
   ├─ Add environment variables
   └─ Wait for green status

4. Deploy Frontend
   ├─ Import repo on Vercel
   ├─ Set root directory: ./frontend
   ├─ Add NEXT_PUBLIC_API_BASE
   └─ Deploy

5. Test Live App
   ├─ Visit Vercel URL
   ├─ Login with credentials
   └─ Test all features

6. Monitor
   ├─ Check Render logs
   ├─ Monitor Vercel analytics
   └─ Fix issues as they appear
```

---

## 🆘 COMMON ISSUES & SOLUTIONS

### Issue: "Cannot GET /home"
**Cause**: Environment variable not set or wrong backend URL
**Fix**:
1. Check NEXT_PUBLIC_API_BASE on Vercel
2. Verify it matches your Render backend URL
3. Redeploy frontend

### Issue: "Cannot connect to database"
**Cause**: DATABASE_URL incorrect or PostgreSQL not running
**Fix**:
1. Verify DATABASE_URL in Render environment
2. Check PostgreSQL status in Render dashboard
3. Restart web service

### Issue: "502 Bad Gateway"
**Cause**: Backend crashed or not responding
**Fix**:
1. Check Render logs for errors
2. Wait for cold start to complete (60 sec)
3. Restart web service

### Issue: "No users found"
**Cause**: Database empty or seeding failed
**Fix**:
1. Check backend logs for "Seeding users" message
2. Wait for first startup (2-3 min)
3. Refresh page

### Issue: Slow performance (30+ sec load)
**Cause**: Render free tier cold start
**Note**: Normal! Free tier spins down after inactivity
**Workaround**: Upgrade to paid tier or just wait

---

## 🔐 SECURITY NOTES

```yaml
Production Deployment:
  ✅ HTTPS enabled (automatic on both platforms)
  ✅ Environment variables secured
  ⚠️ Default credentials should be changed
  ⚠️ No authentication for admin panel in demo

Next Steps:
  - Add 2FA for admin login
  - Change default admin password
  - Add rate limiting
  - Set up monitoring
  - Regular backups
```

---

## 💡 PERFORMANCE OPTIMIZATION (Optional)

### To Remove Cold Starts:
```yaml
Render Upgrade to Basic:
  Cost: $7/month
  Benefit: No spin-down, always running

PostgreSQL Upgrade:
  Cost: $15/month
  Benefit: More storage, better performance
```

### To Speed Up Frontend:
```yaml
Vercel Pro:
  Cost: $20/month
  Benefit: Advanced caching, edge functions

Or:
  Keep free tier (usually fast enough)
```

---

## 📞 SUPPORT & RESOURCES

### Official Docs:
- Render: https://render.com/docs
- Vercel: https://vercel.com/docs
- Next.js: https://nextjs.org/docs
- FastAPI: https://fastapi.tiangolo.com

### Status Pages:
- Render: https://status.render.com
- Vercel: https://www.vercelstatus.com

### Community:
- Reddit: r/webdev, r/nextjs, r/FastAPI
- Discord: Many communities available
- Stack Overflow: Search common issues

---

Generated: 2024
For: StreamRec Movie Recommendation Engine
