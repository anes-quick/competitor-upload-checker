# Duplicate video cards – why it happens and fix

## What you see

- Same video card appears twice (above each other) in a channel’s row.
- Happens **rarely**, often on **first load of the day**.
- **Refresh fixes it** and it stays correct afterward.

## Cause: two `loadAllChannels()` runs at once

The feed is built by one async function, `loadAllChannels()`:

1. It clears the feed and creates one block per channel (each with a `grid-{channelId}`).
2. For each channel it **awaits** the backend (fetch recent videos), then appends cards to that channel’s grid.

If `loadAllChannels()` is started **twice** before the first run finishes (e.g. two inits or init + Refresh), then:

- **Run A:** Clears feed, creates blocks, starts fetching.
- **Run B:** Clears feed again (removes A’s blocks), creates new blocks, starts fetching.
- **Run A’s fetch** finishes. It does `getElementById('grid-Channel1')` and gets **Run B’s** grid (because A’s DOM was replaced). It appends its videos there.
- **Run B’s fetch** finishes and appends its videos to the **same** grid.
- Result: that channel’s grid has videos from both runs → **duplicate cards**.

So duplicates are a **frontend race**: two overlapping runs of `loadAllChannels()` both appending to the same grid elements.

## When can two runs happen?

- **First load of the day:** Browser **back‑forward cache (bfcache)** can restore the page and run scripts again. So you get a second `init()` → second `loadAllChannels()` while the first is still loading → race.
- **Quick double action:** Clicking Refresh (or Add channel / Add back from recent) while the first load is still in progress can start a second `loadAllChannels()`.

## Fix

- **Reentrancy guard:** Only allow one `loadAllChannels()` run at a time. If it’s already running, ignore the new call (or, if we want, we could set a “reload when done” flag and run again after the current run finishes).
- We already have **per‑channel dedup** (`seenIds`) so the **YouTube response** for a single run doesn’t produce duplicates. The guard prevents **two runs** from both appending to the same grid.

Implementing the guard in `competitor-tracker.html` (see code there).
