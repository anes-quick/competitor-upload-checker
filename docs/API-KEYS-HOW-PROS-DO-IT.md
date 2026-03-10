# How professionals store API keys (and keep them safe)

Your API key is **never** committed to git. It stays in environment variables or a secrets store.

---

## 1. **Environment variables (what you’re doing)**

- **Local:** `.env` file in the project, **gitignored**. The app loads it with `python-dotenv` (or similar). Nobody pushes `.env` to the repo.
- **Production (e.g. Railway):** You set variables in the dashboard (Railway → your service → Variables). The host injects them at runtime; they’re not in the code or repo.

This is the standard, simple approach and is what we’re using.

---

## 2. **Secrets managers (bigger / team setups)**

When many apps or people need the same secrets, or audits matter, teams use a **secrets manager**. The app (or the host) fetches secrets at runtime; the key is never in code or in git.

| Tool | Use case |
|------|----------|
| **AWS Secrets Manager** / **Parameter Store** | Apps on AWS |
| **HashiCorp Vault** | On‑prem / multi‑cloud, strict access control |
| **Doppler**, **Infisical** | SaaS: one dashboard, inject into Railway/Vercel/local |
| **GitHub Secrets** | Only for CI/CD (e.g. build/deploy), not for app runtime |
| **Railway / Vercel env vars** | Built‑in “secrets”: you type the value in the UI, it’s encrypted and not in git |

So: **no special app required** for your case; Railway’s Variables *are* the “safe place” for the key in production. Secrets managers are for when you have many services, compliance, or rotation.

---

## 3. **Rules of thumb**

- **Never** commit API keys, passwords, or tokens to git (even in “private” repos).
- **Do** keep them in env vars or a secrets manager, and **do** keep `.env` and `notes` in `.gitignore`.
- If a key ever gets pushed by mistake: revoke/regenerate it in the provider (e.g. Google Cloud Console) and add the file to `.gitignore` so it doesn’t happen again.

---

For this tool: **local** = `.env` (gitignored); **production** = Railway Variables. No extra software needed.
