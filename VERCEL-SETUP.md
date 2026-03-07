# Vercel setup – frontend (Competitor Upload Checker)

Your backend is already on Railway. Follow these steps to put the frontend on Vercel so you (and your VA) can use the tool from a single URL.

---

## 1. Account and connect repo

1. Go to **https://vercel.com** and sign in (choose **Continue with GitHub**).
2. If asked, authorize Vercel to access your GitHub account and repos.
3. Click **Add New…** → **Project**.
4. **Import** the repo **anes-quick/competitor-upload-checker**. If you don’t see it, click **Adjust GitHub App Permissions** and grant Vercel access to that repo, then try again.

---

## 2. Configure the project

1. **Project Name:** leave as is (e.g. `competitor-upload-checker`) or rename if you like.
2. **Root Directory:** leave **empty** (we use the repo root; the frontend files and `vercel.json` are there).
3. **Framework Preset:** choose **Other** (or **Vite** only if you had a Vite app; we have plain HTML).
4. **Build and Output Settings:**
   - **Build Command:** leave empty, or set to `echo 'static'`.
   - **Output Directory:** leave empty (Vercel will serve the root as static).
   - **Install Command:** leave empty (no npm install needed).

5. **Environment Variables:** none needed for the frontend; the backend URL is already in the HTML and switches automatically when the site is not on localhost.

6. Click **Deploy**.

---

## 3. After deploy

1. Wait for the build to finish (usually under a minute).
2. Vercel will show a URL like:
   - **https://competitor-upload-checker.vercel.app**  
   or  
   - **https://competitor-upload-checker-xxxx.vercel.app**
3. Open that URL. You should see your app (password gate, then the competitor tracker).
4. **Using the app:** Add your YouTube API key in Settings, add channels, Refresh All, Load transcripts, then paste a US short URL and click Check. The frontend will call the Railway backend automatically.

---

## 4. Root URL → app

A **vercel.json** in the repo is set so that opening the **root** of your Vercel URL (e.g. `https://competitor-upload-checker.vercel.app/`) serves the app. If you prefer to open the file directly, use:

**https://YOUR-VERCEL-URL/competitor-tracker.html**

---

## 5. Backend and CORS

- The frontend already uses **https://competitor-upload-checker-production.up.railway.app** when it’s not running on localhost.
- The Railway backend is configured to allow requests from any **\*.vercel.app** origin. After you change CORS or redeploy the backend, push to GitHub so Railway redeploys with the new CORS.

---

## 6. Share with your VA

Send your VA the **Vercel URL** (e.g. `https://competitor-upload-checker.vercel.app`). They open it in the browser, enter the password and API key (if you use them), and use the tool like a normal website. No install, no local backend.

---

## Summary

| Step | Action |
|------|--------|
| 1 | Vercel → Add New → Project → Import **anes-quick/competitor-upload-checker** |
| 2 | Root Directory: leave empty. Framework: Other. Build/Install: empty. Deploy. |
| 3 | Open the Vercel URL and test the app. |
| 4 | Share the Vercel URL with your VA. |

After the first deploy, every **git push** to `main` will trigger a new Vercel deployment automatically (if you left the default “Production” branch as `main`).
