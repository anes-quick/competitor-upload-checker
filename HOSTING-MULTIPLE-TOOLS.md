# Hosting multiple tools (Vercel + Railway)

Quick reference for running several tools (each with its own frontend + optional backend) without big cost.

## Vercel (frontends)

- **Free Hobby plan:** Many projects (on the order of hundreds). One project per tool = one URL per tool (e.g. `tool1.vercel.app`, `tool2.vercel.app`).
- **Cost:** $0 for typical personal/small business use. No need to pay unless you need Pro features.

## Railway (backends)

- **Free tier:** Very limited (e.g. one project after trial). Good for a single backend.
- **Option A – One project, multiple services:** Create one Railway project. Add one **service** per tool (each service = one repo or one root directory). So one “project” can run several backends (each with its own URL). Fits within free-tier limits if you stay within usage.
- **Option B – Paid:** More projects and resources; cost scales with usage. Check railway.com/pricing.

**Practical approach:** One Vercel account (many frontends), one Railway project with one service per tool backend. Add a second project or paid plan only when you need it.

## Flow per new tool

1. Copy the **tool-template** folder into a new Cursor project.
2. Build the tool (frontend + backend).
3. Push to GitHub. Connect the **same** repo to Vercel (new project) and to Railway (new service in the same project, or new project if you’re on paid).
4. Set the frontend’s `BACKEND_URL` to that tool’s Railway backend URL.
5. Later: add a homepage and a shared nav bar to every tool; link everything from the hub.
