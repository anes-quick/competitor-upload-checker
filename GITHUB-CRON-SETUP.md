# GitHub Cron Setup (Warm Transcripts)

This repo includes `.github/workflows/cron-warm-transcripts.yml`.

## 1) Add GitHub repository secrets

In GitHub: `Repo -> Settings -> Secrets and variables -> Actions -> New repository secret`

- `CRON_SECRET`  
  Use the same value as Railway backend `CRON_SECRET` (example: `warm_9f2KpL7x_2026`).

- `CRON_WARM_URL`  
  Example:
  `https://competitor-upload-checker-production.up.railway.app/api/cron/warm-transcripts?max_results=5`

## 2) Schedule

Current workflow schedule:
- `30 4,12 * * *` (UTC)
- Equivalent: 06:30 and 14:30 CEST (summer time)

When winter time starts, change to:
- `30 5,13 * * *` (UTC)

## 3) Manual test

Go to `Actions -> Cron Warm Transcripts -> Run workflow`.
Then check Railway logs for:
- `POST /api/cron/warm-transcripts`

