# Backend – Competitor Upload Checker

This is the backend service for the Competitor Upload Checker. It provides a FastAPI-based HTTP API that the frontend can call for tasks like fetching transcripts and performing fuzzy matching.

The goal is to keep the backend self-contained, reproducible, and easy to deploy.

---

## 1. Layout

```text
backend/
  app/
    __init__.py      # App package
    main.py          # FastAPI app factory and ASGI entrypoint
    api/             # API routers (endpoints)
      __init__.py    # Health check + future routes
    services/        # Business logic modules (transcripts, matching, etc.)
  tests/
    test_health.py   # Basic health-check test
  requirements.txt   # Python dependencies (pinned versions)
  .gitignore         # Ignore venv, caches, env files
  README.md          # This file
```

---

## 2. Python version

Use **Python 3.9+** (requirements are pinned for 3.9 compatibility).

You can check your Python version with:

```bash
python3 --version
```

---

## 3. Virtual environment setup

Create and activate a virtual environment **inside** the `backend/` folder so dependencies stay isolated and do not pollute your system Python:

```bash
cd "/Users/anes/Documents/Vibe Coding stuff/Competitor Upload Checker/backend"

# Create venv (one-time)
python3 -m venv .venv

# Activate venv (macOS / zsh)
source .venv/bin/activate
```

You should see `(.venv)` at the start of your terminal prompt when it is active.

> Always make sure the venv is activated before running `pip install` or backend commands.

---

## 4. Install dependencies

With the virtual environment active:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This installs:

- `fastapi==0.128.8` – Web framework for the API.
- `uvicorn[standard]==0.30.6` – ASGI server to run the app.
- `youtube-transcript-api==1.2.4` – Library to fetch YouTube transcripts (to be used in `services/` soon).

---

## 5. Running the backend locally

With the venv active and dependencies installed:

```bash
cd "/Users/anes/Documents/Vibe Coding stuff/Competitor Upload Checker/backend"
uvicorn app.main:app --reload --port 8001
```

Then open in your browser:

- Health check: `http://localhost:8001/api/health`

You should see:

```json
{"status": "ok"}
```

---

## 6. Running tests

Install `pytest` into the venv (if not already installed):

```bash
pip install pytest
```

Then run:

```bash
cd "/Users/anes/Documents/Vibe Coding stuff/Competitor Upload Checker/backend"
pytest
```

You should see the `test_health.py` test pass.

---

## 7. Next steps (for this project)

1. Add a `services/transcripts.py` module that uses `youtube-transcript-api` to fetch transcripts by video ID.
2. Add an `/api/transcript` endpoint that calls the service and returns transcript text + language.
3. Later, add matching/translation endpoints and wire them to the frontend.

This foundation aligns with a typical professional FastAPI backend structure and will make deployment to platforms like Render or Railway straightforward.

---

## 8. Reliable transcripts (avoid blocking)

**Option A: FetchTranscript.com API (recommended for production)**

Set **`FETCHTRANSCRIPT_API_KEY`** in your environment (e.g. in Railway → Variables). The backend will use [FetchTranscript](https://fetchtranscript.com/) instead of scraping YouTube directly. They handle rate limits and blocking on their side; you get a stable API.

- **Cost:** $1 per 1,000 calls; 25 free calls/month. Only successful calls are billed.
- **Setup:** Sign up at fetchtranscript.com, get an API key (starts with `yt_`), add it as `FETCHTRANSCRIPT_API_KEY` in Railway (or your host), redeploy. No proxy needed.
- See **TRANSCRIPT-RELIABILITY-RESEARCH.md** in the project root for how other SaaS products solve this.

**Option B: Run the backend in the cloud (your IP not used)**

Deploy this backend to a free or cheap host so **all transcript traffic uses the server’s IP**, not yours:

- **Railway** – Connect the repo, add a start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Set the frontend’s `BACKEND_URL` to the deployed URL.
- **Render** – New Web Service, connect repo, build: `pip install -r requirements.txt`, start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
- **Fly.io** – Use their Python/FastAPI guide; expose the app and point the frontend to the generated URL.

No code changes needed. Your business IP is never used for transcript requests. (You can still hit YouTube’s limits on the server’s IP; use Option A for reliability.)

**Option C: Use a proxy (optional, can be flaky)**

If you keep running the backend on your machine, you can send transcript requests through a proxy so YouTube sees the proxy’s IP instead of yours:

1. Set one of these environment variables before starting the backend:
   - **`YOUTUBE_TRANSCRIPT_PROXY`** – single URL used for both HTTP and HTTPS, e.g.  
     `YOUTUBE_TRANSCRIPT_PROXY=https://user:pass@proxy.example.com:8080`
   - Or **`HTTP_PROXY`** / **`HTTPS_PROXY`** – standard proxy env vars (same format as above).

2. Start the backend as usual (e.g. with the venv activated). All transcript fetches will go through the proxy.

Examples:

- **Paid residential proxies** (e.g. Webshare): use their HTTP/HTTPS endpoint as `YOUTUBE_TRANSCRIPT_PROXY`.
- **Your own proxy**: run a small proxy (e.g. on a $5 VPS or a cloud box) and set `YOUTUBE_TRANSCRIPT_PROXY` to that URL.
- **VPN**: if your VPN is system-wide, the backend already uses it; no env var needed. To use a different proxy only for this app, set `YOUTUBE_TRANSCRIPT_PROXY` to the VPN’s proxy address if it exposes one.

The proxy is optional. If none of these variables are set, the backend talks to YouTube directly from the machine it runs on.

