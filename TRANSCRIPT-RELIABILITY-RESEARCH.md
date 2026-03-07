# How others fix YouTube transcript / scraping reliability

Summary of how SaaS apps and tools avoid YouTube rate limits and blocking so the tool can be used without constant “wait” or “proxy 502” issues.

---

## 1. What actually causes the problem

- **Unofficial access:** Our app uses `youtube-transcript-api`, which talks to YouTube’s non-public transcript endpoints. YouTube can throttle or block by IP.
- **Single IP:** When the backend (or a single proxy) sends many requests from one IP, that IP hits limits → “temporarily blocking” or proxy 502.
- **Official API:** YouTube Data API v3 has a **captions** feature but needs **OAuth and ownership/edit rights** on the video. It’s not for “get transcript of any public video,” so it doesn’t replace what we need.

---

## 2. What other products do

### A. Proxy rotation (what we tried)

- Use **rotating residential proxies** (e.g. Webshare, Bright Data) so each request can use a different IP.
- **Pros:** No per-request fee; you only pay for proxy traffic.
- **Cons:** Proxies can return 502/errors; you depend on proxy uptime and correct config; some providers are flaky for HTTPS/YouTube.

### B. Third‑party transcript APIs (most reliable for “just get transcript”)

SaaS products that need **reliable** transcripts often use a **managed transcript API** instead of scraping themselves:

| Service | How it helps | Typical cost |
|--------|----------------|--------------|
| **FetchTranscript** | Their servers talk to YouTube; you call their API. No blocks on your side. | $1/1,000 calls, 25 free/month |
| **VCyon** | Same idea; “no rate limits” from your perspective. | 100 free credits, then paid |
| **YouTubeTranscript.dev** | Managed API; they handle limits and blocking. | Free tier + paid |
| **Apify YouTube Transcript Actor** | Runs on Apify’s infra and proxies. | ~$10/1,000 results |

They run the scraping/proxy layer; you get a stable API. Your backend only calls **them**, so YouTube never sees your IP and you don’t manage proxies.

### C. Scraper APIs (generic “we proxy for you”)

- **ScraperAPI, Apify, etc.** send your HTTP requests through their proxy/rotation pool so **your** IP never hits the target.
- Same idea as (B) but generic: you’d still use something like `youtube-transcript-api` and put their proxy in front. Can reduce blocks; 502s can still happen if their proxy has issues.

### D. Official API where it fits

- For **channel lists, thumbnails, metadata** we already use the **YouTube Data API** with an API key. Quota-limited but stable.
- For **“transcript of any public video”** there is no official, unauthenticated API. So (B) or (C) is what others use.

---

## 3. What fits our tool best

- **Goal:** VA can use the tool without “blocked / wait” or “proxy 502” all the time.
- **Best tradeoff:** Add a **reliable transcript source** that doesn’t depend on our proxy:
  - **Option 1 (recommended):** Use a **third‑party transcript API** (e.g. FetchTranscript) when an API key is set. They handle YouTube and blocking; we just call their API. Low cost ($1/1k), 25 free/month.
  - **Option 2:** Keep proxy as an option for high volume / cost-sensitive use, but make it **optional** and document that 502s can happen; primary path = transcript API.

So: **other SaaS fix it by not scraping YouTube themselves** — they use a transcript API or a scraper/proxy API. We do the same by adding FetchTranscript (or similar) as the main, reliable path.

---

## 4. Implemented in this project

- **Backend** uses **FetchTranscript.com** when `FETCHTRANSCRIPT_API_KEY` is set (e.g. in Railway → Variables). All transcript requests then go to their API; no YouTube blocking, no proxy needed.
- **Fallback:** If the key is not set, the app uses `youtube-transcript-api` (and optional `YOUTUBE_TRANSCRIPT_PROXY`). So you can run without paying until you need reliability, then add the key.

**Setup:** Sign up at [fetchtranscript.com](https://fetchtranscript.com), create an API key, add `FETCHTRANSCRIPT_API_KEY` to your backend environment, redeploy. See backend README section 8.
