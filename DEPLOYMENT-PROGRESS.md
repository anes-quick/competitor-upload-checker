# Deployment progress – Vercel + Railway

**Strategy:** Option A (split). Frontend on **Vercel**, backend on **Railway**.  
**Goal:** Share the tool with VA via a normal URL; transcript requests use Railway’s IP, not yours.

Use this file to track where we are and what’s next. Update the checkboxes and “Current step” as we go.

---

## Platform choice

| Role    | Platform | Purpose                          |
|---------|----------|-----------------------------------|
| Frontend | **Vercel**  | Host `competitor-tracker.html` (static) |
| Backend  | **Railway** | Host FastAPI (transcripts, matching, cache) |

---

## Backend (Railway)

- [ ] **1.** Create Railway account (railway.app), install Railway CLI if you want deploy from terminal.
- [ ] **2.** New project → deploy from GitHub (or “Deploy from GitHub” and connect this repo), or upload `backend/` as a service.
- [ ] **3.** Set **root/build** so Railway uses the `backend` folder (or repo root if backend is at root).
  - Build command: e.g. leave default or `pip install -r requirements.txt` if needed.
  - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
  - If backend lives in `backend/`: set **Root Directory** to `backend` in Railway, so start stays `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
- [ ] **4.** Add **Environment variables** in Railway if needed (e.g. `YOUTUBE_TRANSCRIPT_PROXY` only if using a proxy).
- [ ] **5.** Deploy and get the public URL (e.g. `https://your-app.up.railway.app`). Note it as **BACKEND_URL** for frontend.
- [ ] **6.** Test: open `https://<BACKEND_URL>/api/health` → should return `{"status":"ok"}`.

---

## Frontend (Vercel)

- [ ] **7.** Create Vercel account (vercel.com), connect GitHub (or use Vercel CLI).
- [ ] **8.** New project → import this repo (or the folder that contains `competitor-tracker.html`).
- [ ] **9.** Configure project:
  - **Root Directory:** project root (where `competitor-tracker.html` lives).
  - **Build:** static site; build command can be empty or `echo 'static'`.
  - **Output:** single HTML or static; Vercel usually auto-detects.
- [ ] **10.** Set **BACKEND_URL** for production:
  - In code: `competitor-tracker.html` uses a single `BACKEND_URL` (e.g. `const BACKEND_URL = '...'`).
  - Either hardcode the Railway URL in the file before deploy, or use Vercel **Environment Variable** and inject it at build time (would require a tiny build step). For simplicity, first deploy with **hardcoded Railway URL** in `competitor-tracker.html`, then we can switch to env later.
- [ ] **11.** Deploy. Note the frontend URL (e.g. `https://your-project.vercel.app`).

---

## CORS

- [ ] **12.** In **backend** (Railway), allow the Vercel frontend origin in CORS.
  - In `backend/app/main.py`: add the Vercel URL (e.g. `https://your-project.vercel.app`) to `allow_origins` (and optionally `http://localhost:8000` for local dev).
- [ ] **13.** Redeploy backend so CORS change is live.

---

## Testing (production)

- [ ] **14.** Open the **Vercel frontend URL** in the browser.
- [ ] **15.** Test: Settings (API key, password), add a channel, “Refresh All”, “Load transcripts”, “Check” with a US short URL. Confirm no CORS errors and that results load.

---

## Sharing with VA

- [ ] **16.** Share the **frontend URL** (Vercel) with your VA.
- [ ] **17.** (Optional) Add short instructions: where to set API key, how to add channels, how to paste US link and read the “already uploaded?” result.

---

## Current step

**Next:** Start with **Backend (Railway)** steps 1–6. Once backend URL is known, do **Frontend (Vercel)** 7–11, then **CORS** 12–13, then **Testing** 14–15.

---

## URLs (fill in after deploy)

| What     | URL |
|----------|-----|
| Backend  | `https://_______________.up.railway.app` |
| Frontend | `https://_______________.vercel.app` |

---

## Notes

- Backend runs on Railway → transcript requests use Railway’s IP (not yours).
- To deploy updates later: push to Git (if connected) or run Railway/Vercel deploy from Cursor; tell the AI “deploy” and we run the right commands.
- Roadmap section **7) Deployment & sharing** is tracked here; see `roadmap.txt` for full product roadmap.
