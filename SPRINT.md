# Competitor Tracker – Sprint & version log

Track improvements and versions (1.1, 1.2, …). Check off when done.

---

## Version 1.1 (current focus)

| # | Task | Status |
|---|------|--------|
| 1 | Move API key to backend (set once in Railway, no key in frontend) | ✅ |
| 2 | Improve accuracy for checking | 🔲 |
| 3 | Colored red box around similar videos | 🔲 |
| 4 | Fix double amount of videos issue | ✅ |
| 5 | Remove password entry (make it one-time only) | ✅ |

---

## Done (pre-sprint)

- Deploy (Vercel + Railway), FetchTranscript, multi-language transcripts
- Recent channels (re-add removed), transcript cache status (cached vs to load)
- Green transcript buttons, dedupe videos per channel

---

## Changelog

- **v1.1 (current)** — API key moved to backend: set `YOUTUBE_API_KEY` in Railway once; frontend no longer asks for or stores the key. Add channel & Refresh All go through backend.

---

## How to use

- **Version:** Bump when we ship a set of changes (e.g. 1.1 → 1.2).
- **Status:** 🔲 = to do, 🔄 = in progress, ✅ = done.
- Update this file as we complete each item.
