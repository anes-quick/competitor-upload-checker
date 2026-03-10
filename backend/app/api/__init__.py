from __future__ import annotations

import asyncio
import os
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.transcripts import (
    get_transcript,
    get_transcript_cached,
    cache_stats,
)
from app.services.translate import translate_to_german
from app.services.matching import find_matches
from app.services import youtube_data as yt


router = APIRouter()

# Seconds to wait after each successful transcript fetch when warming (avoids YouTube rate limit)
WARM_DELAY_SEC = 4

# Progress state for background warm task (so frontend can poll)
_warm_state: dict = {"in_progress": False, "total": 0, "warmed": 0, "failed": 0}


class CompetitorVideo(BaseModel):
    video_id: str
    channel_name: str
    title: str
    channel_id: str


class CheckOriginalRequest(BaseModel):
    us_video_id: str
    competitor_videos: list[CompetitorVideo]


class WarmRequest(BaseModel):
    video_ids: list[str]


@router.get("/health", tags=["system"])
async def health() -> dict:
  """
  Simple health check endpoint.

  Useful for uptime checks and verifying deployments.
  """
  return {"status": "ok"}


# ─── YouTube Data API proxy (API key on backend only) ───────────────────────────

@router.get("/youtube/resolve-channel", tags=["youtube"])
async def youtube_resolve_channel(url: str = Query(..., min_length=1)) -> dict:
  """Resolve a channel URL to channelId, name, thumb. Uses backend YOUTUBE_API_KEY."""
  try:
    return await asyncio.to_thread(yt.resolve_channel, url)
  except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))


@router.get("/youtube/channels/{channel_id}/recent-videos", tags=["youtube"])
async def youtube_recent_videos(
  channel_id: str,
  max_results: int = Query(10, ge=1, le=50),
) -> dict:
  """Get recent uploads for a channel. Returns playlistItems (snippet) list."""
  try:
    playlist_id = await asyncio.to_thread(yt.get_uploads_playlist_id, channel_id)
    items = await asyncio.to_thread(yt.get_recent_videos, playlist_id, max_results)
    return {"items": items}
  except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))


@router.post("/restart", tags=["system"])
async def restart() -> dict:
  """
  Shut down the backend process after a short delay (so the response can be sent).
  If you run the backend with a restart loop (e.g. while true; do uvicorn ...; done)
  or a process manager, it will come back automatically.
  """
  async def _exit_after_response() -> None:
    await asyncio.sleep(1)
    os._exit(0)
  asyncio.create_task(_exit_after_response())
  return {"status": "restarting"}


@router.get("/transcript", tags=["transcripts"])
async def transcript(video_id: str = Query(..., min_length=1, description="YouTube video ID")) -> dict:
  """
  Fetch transcript for a YouTube video.

  Returns transcript text and detected language, or 400 if unavailable.
  """
  try:
    result = get_transcript(video_id)
    return result
  except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
  except Exception as e:
    err_msg = str(e)
    if "502" in err_msg and ("roxy" in err_msg or "Gateway" in err_msg):
      raise HTTPException(
        status_code=502,
        detail="Proxy returned 502 Bad Gateway. Try again in a moment, or remove YOUTUBE_TRANSCRIPT_PROXY in Railway to use direct connection (may hit YouTube limits).",
      )
    raise HTTPException(status_code=502, detail=f"Transcript fetch error: {err_msg[:200]}")


async def _run_warm_task(video_ids: list[str]) -> None:
  global _warm_state
  _warm_state["in_progress"] = True
  _warm_state["total"] = len([v for v in video_ids if v and get_transcript_cached(v) is None])
  _warm_state["warmed"] = 0
  _warm_state["failed"] = 0
  try:
    for video_id in video_ids:
      if not video_id or get_transcript_cached(video_id) is not None:
        continue
      try:
        await asyncio.to_thread(get_transcript, video_id, "de")
        _warm_state["warmed"] += 1
        await asyncio.sleep(WARM_DELAY_SEC)  # only delay after a successful fetch
      except ValueError:
        _warm_state["failed"] += 1
  finally:
    _warm_state["in_progress"] = False


@router.post("/transcripts/warm", tags=["transcripts"])
async def warm_transcripts(req: WarmRequest) -> dict:
  """
  Start pre-fetching transcripts in the background. Returns immediately.
  Poll GET /transcripts/warm/status for progress.
  """
  if _warm_state.get("in_progress"):
    return {"status": "already_running", "total": _warm_state["total"], "warmed": _warm_state["warmed"], "failed": _warm_state["failed"]}
  to_fetch = [v for v in req.video_ids if v and get_transcript_cached(v) is None]
  asyncio.create_task(_run_warm_task(req.video_ids))
  return {"status": "started", "total": len(to_fetch)}


@router.get("/transcripts/warm/status", tags=["transcripts"])
async def warm_status() -> dict:
  """Return current warm task progress for the loading bar."""
  return dict(_warm_state)


@router.get("/transcripts/cache", tags=["transcripts"])
async def get_cache_status() -> dict:
  """Return how many competitor transcripts are cached."""
  return cache_stats()


@router.post("/check-original", tags=["transcripts"])
async def check_original(req: CheckOriginalRequest) -> dict:
  """
  Check if any competitor has already uploaded content similar to the US video.

  Fetches US transcript, translates to German, fetches competitor transcripts,
  and returns fuzzy matches.
  """
  try:
    us_result = get_transcript(req.us_video_id)
    us_text = us_result.get("transcript", "") or ""
    us_lang = us_result.get("language", "unknown")

    if not us_text.strip():
      return {"matches": [], "us_transcript_preview": "", "translated_preview": "", "error": "US transcript is empty"}

    # Translate to German for matching
    translated = translate_to_german(us_text)

    # Use cached competitor transcripts only (no fetches here = no rate limit)
    candidates = []
    for cv in req.competitor_videos:
      ct = get_transcript_cached(cv.video_id)
      if not ct:
        continue
      candidates.append({
        "video_id": cv.video_id,
        "channel_name": cv.channel_name,
        "title": cv.title,
        "channel_id": cv.channel_id,
        "transcript": ct.get("transcript", "") or "",
      })
    if req.competitor_videos and not candidates:
      raise HTTPException(
        status_code=400,
        detail="No competitor transcripts in cache. Load transcripts first (click 'Load transcripts' after refreshing the feed).",
      )
    matches = find_matches(translated, candidates)

    return {
      "matches": matches,
      "us_transcript_preview": us_text[:300] + ("…" if len(us_text) > 300 else ""),
      "translated_preview": translated[:300] + ("…" if len(translated) > 300 else ""),
    }
  except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
  except Exception as e:
    raise HTTPException(status_code=502, detail=f"Transcript service error: {getattr(e, 'message', str(e))}")

