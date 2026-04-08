# Railway setup – backend (Competitor Upload Checker)

Follow these steps to get your FastAPI backend running on Railway. When done, you’ll have a public URL like `https://your-app.up.railway.app`.

---

## 1. Account and project

1. Go to **https://railway.app** and sign in (GitHub recommended).
2. Click **“New Project”**.
3. Choose **“Deploy from GitHub repo”** (if your project is on GitHub), or **“Empty project”** if you’ll deploy another way (e.g. CLI).

---

## 2. Connect the repo (GitHub)

1. If you chose “Deploy from GitHub repo”:
   - Select the repo that contains this project (the one with the `backend` folder).
   - Authorize Railway if asked.
2. Railway will add a **service** to the project. We’ll configure it in the next step.

If the project is **not** on GitHub yet:
- Create a repo, push your code, then connect that repo in Railway, **or**
- Use the Railway CLI (see section 6 below) to deploy from your machine.

---

## 3. Configure the service (root + start)

1. Click the new **service** (the box that appeared).
2. Open **Settings** (or the “Settings” tab).
3. **Root Directory**
   - Set **Root Directory** to: `backend`
   - So Railway runs everything from the `backend` folder (where `requirements.txt` and `app/` live).
4. **Build**
   - Railway usually detects Python. If there’s a build step, it can be:
     - **Build Command:** `pip install -r requirements.txt`
     - or leave empty and let Railway use `requirements.txt` automatically.
5. **Start Command**
   - Set **Start Command** to:
     ```bash
     uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```
   - Railway sets `PORT`; your app must listen on `0.0.0.0` and this port.

6. **Save** / apply changes.

---

## 4. Environment variables

- In the same service, open **Variables** (or “Environment”).
- Common variables:
  - `YOUTUBE_API_KEY` = YouTube Data API key (for loading channel videos)
  - `TRANSCRIPTAPI_API_KEY` = primary transcript provider
  - `FETCHTRANSCRIPT_API_KEY` = transcript fallback provider
  - `YOUTUBE_TRANSCRIPT_PROXY` = optional proxy URL
- For Railway cron warmup automation, also add:
  - `CRON_SECRET` = random secret string
  - `TRACKED_CHANNEL_IDS` = optional fallback list (usually not needed once frontend sync is active)
  - `CRON_RECENT_UPLOADS_PER_CHANNEL` = optional per-channel count (e.g. `5`)

---

## 5. Deploy and get the URL

1. If you connected a GitHub repo: push a commit or trigger **Deploy** in Railway (e.g. “Deploy” or “Redeploy”).
2. Wait for the build and deploy to finish (logs in the “Deployments” or “Logs” tab).
3. **Generate a public URL:**
   - Open the **Settings** of the service (or the “Settings” tab).
   - Find **Networking** or **Public Networking**.
   - Click **“Generate domain”** (or “Add domain”). Railway will give you a URL like:
     `https://competitor-upload-checker-backend-production-xxxx.up.railway.app`
4. Copy that URL — this is your **BACKEND_URL**. Use it in the frontend (e.g. in `competitor-tracker.html` or as Vercel env).

---

## 6. Test the backend

Open in the browser (replace with your real URL):

```text
https://YOUR-RAILWAY-URL/api/health
```

You should see:

```json
{"status":"ok"}
```

For cron warm trigger (manual test):

```bash
curl -X POST "https://YOUR-RAILWAY-URL/api/cron/warm-transcripts" \
  -H "X-Cron-Secret: YOUR_CRON_SECRET"
```

If that works, the backend is set up correctly.

---

## 7. Deploy without GitHub (Railway CLI)

If you prefer not to use GitHub:

1. Install the CLI: **https://docs.railway.app/develop/cli**
   - e.g. `npm i -g @railway/cli` or use the install command for your OS.
2. Log in: `railway login`.
3. In your project folder (the **repo root**, not inside `backend`), run:
   ```bash
   railway link
   ```
   Create or select a project.
4. Deploy only the backend:
   ```bash
   railway up --service backend
   ```
   Or if the CLI is running from the repo root, you may need to specify the directory. Check the docs for `railway up` and “root directory” for your Railway project.

Alternatively, in the Railway dashboard you can use **“Deploy from local”** and upload or point to your `backend` folder if that option is available.

---

## Summary

| Setting           | Value |
|-------------------|--------|
| Root Directory    | `backend` |
| Start Command     | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health check URL  | `https://YOUR-URL/api/health` |

After this, paste your **BACKEND_URL** into `DEPLOYMENT-PROGRESS.md` and continue with the **Frontend (Vercel)** steps there.
