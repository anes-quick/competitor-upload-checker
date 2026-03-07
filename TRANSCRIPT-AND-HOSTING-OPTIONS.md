# Transcript & hosting options – ease, time, cost, workflow

This doc compares ways to avoid YouTube blocks and protect your IP, then explains how your workflow changes when the backend runs in the cloud vs locally.

---

## 1. Ranking: ease, time to set up, cost

All options below achieve: **your IP is not used for transcript requests** (so no risk to your YouTube channel and less blocking).

| Rank | Option | Ease (1–5, 5 = easiest) | Time to set up | Cost | Notes |
|------|--------|--------------------------|-----------------|------|--------|
| **1** | **Run backend in the cloud** (Railway / Render / Fly.io) | **5** | **~15–30 min** (one-time) | **Free** (within free tier) or a few €/month | No proxy, no third-party transcript API. You deploy this repo; transcript requests come from the server’s IP. |
| **2** | **Proxy env var** (e.g. `YOUTUBE_TRANSCRIPT_PROXY`) | **4** | **~5–10 min** | **Free** (your VPN) or **paid** (proxy service) | You already have the code. Set one env var; restart backend. Need a proxy URL (VPN endpoint, VPS, or paid proxy). |
| **3** | **Third-party transcript API** (DownSub, Vizard, EasySubAPI) | **3** | **~30–60 min** (sign up + we add integration) | **Paid** (e.g. DownSub ~$5/mo, others per request) | We’d add an optional “use DownSub/Vizard when API key set.” You depend on their limits and availability. |
| **4** | **Self-hosted “DownSub API”** (e.g. GitHub clone on a VPS) | **2** | **~1–2 hours** (server + deploy + wire our backend to it) | **Free** (if you have free-tier server) or **~$5/mo** VPS | You run someone else’s service on your server; our backend calls that instead of YouTube. More moving parts. |
| **5** | **Run backend locally, no proxy, no cloud** | **5** (easiest to run) | **0** | **Free** | Your IP is used for transcript requests. Easiest to start, but highest risk of blocks and using your “business” IP. |

**Recommendation:**  
- **Easiest and free:** **#1 – run backend in the cloud.**  
- **Quick and local:** **#2 – proxy** (if you have a proxy/VPN URL).  
- **Willing to pay for “someone else’s IP”:** **#3 – DownSub/Vizard API.**

---

## 2. Cost summary (rough)

| Option | Typical cost |
|--------|----------------|
| Backend on **Railway** | Free tier then usage-based (often $0–5/mo for small use). |
| Backend on **Render** | Free tier (with limits); paid from ~$7/mo. |
| Backend on **Fly.io** | Free allowance; then pay-as-you-go. |
| **Proxy** (your VPN) | Already paying for VPN. |
| **Proxy** (paid, e.g. Webshare) | From ~$2–10/mo depending on traffic. |
| **DownSub API** | ~$5/mo (e.g. 2000 credits). |
| **Vizard / EasySubAPI** | Per-request or subscription; check their pricing. |
| **Self-hosted DownSub-style API on VPS** | ~$5/mo (or free tier of a cloud VM). |

---

## 3. How working on the tool changes: local vs cloud

### Running everything **locally** (frontend + backend on your Mac)

- **Editing the tool**
  - You change HTML/JS in `competitor-tracker.html` or Python in `backend/`.
  - You refresh the browser (or restart the backend with “Restart backend” / terminal).
  - You see changes **immediately**. No deploy step.
- **Using the tool**
  - You open the HTML file (e.g. via Live Server or `file://`) and point it at `http://localhost:8001` for the backend.
  - Transcript requests go from **your Mac** → YouTube (so your IP is used unless you use a proxy).
- **Sharing**
  - Only you (on your machine) can use it, unless you expose your Mac to the internet (not recommended).

So: **development is fastest** (edit → refresh), but **your IP is in the loop** unless you use a proxy.

---

### Running the **backend in the cloud** (frontend still local or also hosted)

- **Editing the tool**
  - **Frontend:** You still edit `competitor-tracker.html` locally. If the frontend is only on your machine, you refresh and test as now; if you later put the frontend on a host (e.g. GitHub Pages, Netlify), you **deploy** (e.g. push to Git or upload) to see changes live.
  - **Backend:** You edit code in `backend/` on your machine. To see changes **on the live site**, you must **deploy** the backend again (e.g. push to Git if Railway/Render auto-deploys, or run `railway up` / equivalent). So: **edit locally → deploy → then the cloud backend runs the new code.**
- **Using the tool**
  - You (and anyone you share the link with) open the **frontend** URL. The frontend is configured to call the **cloud backend URL** (e.g. `https://your-app.railway.app`), not localhost.
  - Transcript requests go **cloud server → YouTube**. Your IP is never used for transcripts.
- **Sharing**
  - You can share the frontend URL so others can use the tool without installing anything. They use the same cloud backend.

So: **development is one extra step** (deploy to see backend changes live), but **your IP is protected** and the tool can be used from anywhere.

---

### Side-by-side: what actually changes

| Aspect | Local (backend on your Mac) | Cloud (backend on Railway/Render/Fly) |
|--------|-----------------------------|----------------------------------------|
| **Edit frontend** | Edit file → refresh browser. | Same if frontend is local; if frontend is hosted, deploy to see changes. |
| **Edit backend** | Edit file → restart backend (or “Restart backend” button). | Edit locally → **deploy** (e.g. push to Git or run deploy command) → cloud runs new code. |
| **Time to see backend change** | Seconds (restart). | 1–3 min typically (build + deploy). |
| **Who can use it** | Only you (on your machine). | Anyone with the link (if you share the frontend URL). |
| **Transcript requests** | From your IP (unless you use proxy). | From the server’s IP; your IP not used. |
| **Backend “Restart” button** | Stops backend on your Mac; you start it again in terminal. | Would need to trigger a redeploy (not implemented); usually you just push a new version. |

---

## 4. Practical takeaway

- **Easiest and free way** to protect your IP: **put the backend in the cloud** (e.g. Railway) once; keep editing code on your Mac and deploy when you want the live app updated.
- **Development flow with cloud backend:**  
  - Work on frontend/backend locally as now.  
  - When you’re happy with a change and want the “real” app updated: push to Git (or run your host’s deploy).  
  - No change to how you write code; only an extra “deploy” step to see that code running on the public/live backend.
