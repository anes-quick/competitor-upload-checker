# Get your project onto GitHub

You do this **once**. After that, you push updates from Cursor (or terminal) whenever you want to deploy.

---

## Part A: Create the repo on GitHub (in the browser)

1. Go to **https://github.com** and sign in.
2. Click the **+** (top right) → **New repository**.
3. Fill in:
   - **Repository name:** e.g. `competitor-upload-checker` (or any name you like).
   - **Description:** optional (e.g. "Tool to check if competitors already uploaded a US short").
   - **Public** is fine (your code is visible; we don’t push API keys or secrets).
   - **Do not** check "Add a README", "Add .gitignore", or "Choose a license" — you already have a project. Leave the repo **empty**.
4. Click **Create repository**.
5. On the next page you’ll see "…or push an existing repository from the command line." **Keep that page open** — you’ll need the URL. It looks like:
   ```text
   https://github.com/YOUR-USERNAME/competitor-upload-checker.git
   ```
   Copy that URL (replace YOUR-USERNAME with your GitHub username).

---

## Part B: Put your project in Git and push (in Cursor)

Open the **terminal in Cursor** (Terminal → New Terminal). Make sure you’re in the project folder. Then run these commands **one by one**. If Git says "command not found", see Part C first.

**1. Go to the project folder**
```bash
cd "/Users/anes/Documents/Vibe Coding stuff/Competitor Upload Checker"
```

**2. Turn this folder into a Git repo**
```bash
git init
```

**3. Add all files** (respects .gitignore, so .venv and `notes` won’t be added)
```bash
git add .
```

**4. First save (commit)**
```bash
git commit -m "Initial commit: Competitor Upload Checker frontend and backend"
```

**5. Rename the default branch to main** (GitHub expects `main`)
```bash
git branch -M main
```

**6. Tell Git where GitHub is**  
Replace `YOUR-USERNAME` and `competitor-upload-checker` with your real GitHub username and repo name:
```bash
git remote add origin https://github.com/YOUR-USERNAME/competitor-upload-checker.git
```

**7. Push to GitHub**
```bash
git push -u origin main
```

- If Git asks for **username**: your GitHub username.
- If Git asks for **password**: use a **Personal Access Token**, not your GitHub password. See Part C below.

When the push succeeds, refresh your repo page on GitHub — you’ll see all your files there.

---

## Part C: If something doesn’t work

**"git: command not found"**  
- Install Git: https://git-scm.com/downloads (macOS: often `xcode-select --install` or install Xcode Command Line Tools).
- Restart Cursor and try again.

**Git asks for a password and rejects your GitHub password**  
- GitHub no longer accepts account passwords for push. Use a **Personal Access Token (PAT)**:
  1. GitHub → your profile (top right) → **Settings** → **Developer settings** (left) → **Personal access tokens** → **Tokens (classic)**.
  2. **Generate new token (classic)**. Name it e.g. "Cursor", enable **repo**.
  3. Copy the token (you won’t see it again).
  4. When Git asks for password, **paste the token** (not your GitHub password).
- Or use **GitHub Desktop** or **SSH** later; for now PAT is the simplest.

**"remote: Permission denied" or "Authentication failed"**  
- Double-check the repo URL and that you’re using a PAT as the password.
- Make sure the repo name and username in `git remote add origin ...` match the repo you created.

---

## After the first push

- Your code is on GitHub. You can connect this repo to **Railway** (backend) and **Vercel** (frontend) in their dashboards.
- When you change code and want to update the live app: run `git add .`, then `git commit -m "Describe the change"`, then `git push`. Railway/Vercel will redeploy if connected to this repo.
