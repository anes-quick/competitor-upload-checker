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

## Backend (Railway) ✅

- [x] **1.** Create Railway account (railway.app), install Railway CLI if you want deploy from terminal.
- [x] **2.** New project → deploy from GitHub (or “Deploy from GitHub” and connect this repo), or upload `backend/` as a service.
- [x] **3.** Set **root/build** so Railway uses the `backend` folder (or repo root if backend is at root).
  - Build command: e.g. leave default or `pip install -r requirements.txt` if needed.
  - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
  - If backend lives in `backend/`: set **Root Directory** to `backend` in Railway, so start stays `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
- [x] **4.** Add **Environment variables** in Railway:
  - **YOUTUBE_API_KEY** (required) — for adding channels and loading recent videos. Get from [Google Cloud Console](https://console.cloud.google.com/apis/credentials) (YouTube Data API v3).
  - **YOUTUBE_TRANSCRIPT_PROXY** (optional) — only if using a proxy for transcripts.
  - **FETCHTRANSCRIPT_API_KEY** (optional) — if using FetchTranscript.com for reliable transcripts.
- [x] **5.** Deploy and get the public URL (e.g. `https://your-app.up.railway.app`). Note it as **BACKEND_URL** for frontend.
- [x] **6.** Test: open `https://<BACKEND_URL>/api/health` → should return `{"status":"ok"}`.

---

## Frontend (Vercel) ✅

- [x] **7.** Create Vercel account (vercel.com), connect GitHub (or use Vercel CLI).
- [x] **8.** New project → import this repo (or the folder that contains `competitor-tracker.html`).
- [x] **9.** Configure project:
  - **Root Directory:** project root (where `competitor-tracker.html` lives).
  - **Build:** static site; build command can be empty or `echo 'static'`.
  - **Output:** single HTML or static; Vercel usually auto-detects.
- [x] **10.** Set **BACKEND_URL** for production:
  - In code: `competitor-tracker.html` uses a single `BACKEND_URL` (e.g. `const BACKEND_URL = '...'`).
  - Either hardcode the Railway URL in the file before deploy, or use Vercel **Environment Variable** and inject it at build time (would require a tiny build step). For simplicity, first deploy with **hardcoded Railway URL** in `competitor-tracker.html`, then we can switch to env later.
- [x] **11.** Deploy. Note the frontend URL (e.g. `https://your-project.vercel.app`).

---

## CORS ✅

- [x] **12.** In **backend** (Railway), allow the Vercel frontend origin in CORS.
  - In `backend/app/main.py`: add the Vercel URL (e.g. `https://your-project.vercel.app`) to `allow_origins` (and optionally `http://localhost:8000` for local dev).
- [x] **13.** Redeploy backend so CORS change is live.

---

## Testing (production) ✅

- [x] **14.** Open the **Vercel frontend URL** in the browser.
- [x] **15.** Test: Settings (API key, password), add a channel, “Refresh All”, “Load transcripts”, “Check” with a US short URL. Confirm no CORS errors and that results load.

---

## Sharing with VA

- [ ] **16.** Share the **frontend URL** (Vercel) with your VA.
- [ ] **17.** (Optional) Add short instructions: where to set API key, how to add channels, how to paste US link and read the “already uploaded?” result.

---

## Current step

**Done:** Backend (Railway), Frontend (Vercel), CORS, testing. App is shareable.

**Optional (if YouTube ever blocks Railway’s IP):** Add proxy – see section below and roadmap section 8.

---

## Optional: Avoid YouTube blocking (proxy on Railway)

Your **business IP is already safe** — transcript requests go from Railway’s IP. If YouTube ever rate-limits or blocks Railway’s IP and you see “temporarily blocking” on the app:

1. Get a proxy URL (e.g. paid proxy like Webshare, or a small VPS running a proxy).
2. In **Railway** → your backend service → **Variables** → add:
   - **Name:** `YOUTUBE_TRANSCRIPT_PROXY`
   - **Value:** your proxy URL (e.g. `https://user:pass@proxy.example.com:8080`).
3. Redeploy (or wait for auto-redeploy). All transcript fetches will then go through the proxy; no code or frontend change.

See **roadmap.txt** section 8 and **TRANSCRIPT-AND-HOSTING-OPTIONS.md** for other options (e.g. third-party transcript API).

---

## URLs (fill in after deploy)

| What     | URL |
|----------|-----|
| Backend  | `https://competitor-upload-checker-production.up.railway.app` |
| Frontend | `https://_______________.vercel.app` |

---

## Notes

- Backend runs on Railway → transcript requests use Railway’s IP (not yours).
- To deploy updates later: push to Git (if connected) or run Railway/Vercel deploy from Cursor; tell the AI “deploy” and we run the right commands.
- Roadmap section **7) Deployment & sharing** is tracked here; see `roadmap.txt` for full product roadmap.
