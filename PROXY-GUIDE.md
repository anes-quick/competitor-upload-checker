# Proxy guide – fix “YouTube blocked, had to wait” (Competitor Upload Checker)

If after some “Load transcripts” or checking the tool stops working and says **“YouTube is temporarily blocking…”** and your VA has to wait before it works again, the fix is to send transcript requests through a **proxy**. Best is a **rotating** proxy so each request can use a different IP and no single IP gets rate-limited.

---

## Fix in 3 steps (rotating proxy on Railway)

1. **Get a rotating proxy**  
   Use a provider that gives you **rotating residential** or **rotating datacenter** proxies (different IP per request). Examples:
   - **Webshare** (webshare.io) – Buy “Residential proxies” or “Rotating” plan. In the dashboard you get a proxy URL; for rotation the username is often like `user-rotate` or they give you a rotation endpoint. Check their docs for “rotating” format.
   - **Bright Data, Oxylabs, Smartproxy** – Same idea: rotating proxy product, they give you host, port, username, password (and sometimes a special username for rotation).

2. **Format the proxy URL**  
   You need one URL used for both HTTP and HTTPS, for example:
   ```text
   http://USERNAME:PASSWORD@PROXY_HOST:PORT
   ```
   If the provider uses a **rotating** username (e.g. `user-rotate`), use that in `USERNAME`. Replace `USERNAME`, `PASSWORD`, `PROXY_HOST`, `PORT` with the values from the provider. If they give you an HTTPS proxy URL, you can use that instead of `http://` if our backend supports it (our code uses the same URL for both).

3. **Set it on Railway and redeploy**  
   - Railway → your backend service → **Variables**.
   - Add: **Name** = `YOUTUBE_TRANSCRIPT_PROXY`, **Value** = the proxy URL from step 2.
   - Save / redeploy so the new variable is used.

After that, all transcript requests (Load transcripts + Check) go through the proxy. With **rotating** proxies, each request can use a different IP, so YouTube is much less likely to block and your VA can keep using the tool without long waits.

---

## What actually goes through the proxy?

- **Through the proxy:** Only your **Railway backend** talking to **YouTube** to fetch **transcript text** (captions). So: requests from Railway → proxy → YouTube.
- **Not through the proxy:** Your VA’s browser, passwords, or YouTube API key. The frontend (Vercel) and your API key are used in the browser and when calling your backend; the proxy is only used for backend → YouTube.

So the proxy only sees “this server is asking YouTube for transcript data.” It doesn’t see your app’s password or the YouTube API key.

---

## Do you need one?

- **Yes**, if you already see “YouTube is temporarily blocking…” and your VA has to wait. Use the 3 steps above (rotating proxy on Railway) to fix it.
- **No**, if the app never blocks. Then you can skip the proxy until it happens.

---

## Free proxies

- **Public free proxy lists** (random IPs from the internet):  
  **Not recommended.** They’re often slow, die quickly, and can be run by anyone – so they could log or tamper with traffic. Fine for anonymous browsing, not for something you rely on or care about.
- **Your own “free” option:** Use a **free tier** of a cloud (e.g. Oracle Cloud, Google Cloud, AWS free tier) and run a small proxy (e.g. Squid) on a VM. Then **you** control the proxy; nothing is shared with a random provider. Setup is more technical (server + proxy config).

So: there are no good *zero-setup* free proxies that are both safe and reliable. “Free” usually means shared/public and less safe.

---

## Paid proxies – rotating is what fixes blocking

- **Webshare** (webshare.io) – Has **rotating** plans (residential or datacenter). You get host, port, username, password; for rotation the username is often something like `user-rotate`. From a few €/month. Use the proxy URL in `YOUTUBE_TRANSCRIPT_PROXY` on Railway.
- **Bright Data, Oxylabs, Smartproxy** – Also offer rotating proxies; get the proxy URL from the dashboard and put it in Railway the same way.

**Why rotating?** YouTube limits by IP. If every transcript request comes from the same IP (e.g. Railway’s), that IP gets blocked after a while. With **rotating** proxies, each request can use a different IP, so no single IP hits the limit and the tool keeps working for your VA.

Safety: Only “Railway → YouTube transcript requests” go through the proxy. Your app password and YouTube API key do not. Use a known provider (e.g. Webshare).

---

## Your own proxy (VPS) – max control

- **What:** Rent a small server (e.g. €5/month VPS), install a simple HTTP/HTTPS proxy (e.g. Squid or a tiny Python/Node proxy).  
- **Then:** Set `YOUTUBE_TRANSCRIPT_PROXY` on Railway to that server’s URL.  
- **Safety:** Only your server talks to YouTube; you don’t share traffic with a third-party proxy company. Downside: you have to set up and maintain the server.

---

## Summary

| Option              | Cost        | Safe? | Effort   |
|---------------------|------------|-------|----------|
| No proxy            | Free       | Yes*  | None     |
| Paid (e.g. Webshare)| Few €/mo   | Yes** | Low      |
| Your own VPS proxy  | ~€5/mo     | Yes   | Medium   |
| Free public proxies| Free       | No    | Not recommended |

\* Your IP is already safe; only Railway’s IP hits YouTube.  
\** As long as you use a known provider and don’t send passwords through the proxy (we don’t).

**Recommendation:** To fix “blocked, had to wait” so your VA can use the tool without long waits, use a **rotating paid proxy** (e.g. Webshare rotating), set `YOUTUBE_TRANSCRIPT_PROXY` on Railway, and redeploy. That’s the most direct fix. If you prefer not to use a third-party proxy, run your own proxy on a VPS (single IP, so you may still hit limits under heavy use; rotating is better for avoiding blocks).
