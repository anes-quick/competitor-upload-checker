from __future__ import annotations

import asyncio
import os
import json
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Header
from pydantic import BaseModel

from app.services.transcripts import (
    get_transcript,
    get_transcript_cached,
    cache_stats,
)
from app.services.translate import translate_to_german
from app.services.matching import find_matches, DEFAULT_MATCH_THRESHOLD
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

class IntegrationCheckTextRequest(BaseModel):
    transcript_text: str
    competitor_videos: list[CompetitorVideo]
    source_video_url: Optional[str] = None
    source_title: Optional[str] = None

class TrackedChannel(BaseModel):
    channel_id: str
    name: Optional[str] = None
    url: Optional[str] = None
    thumb: Optional[str] = None

class TrackedChannelsRequest(BaseModel):
    channels: list[TrackedChannel]

_tracked_channels: list[dict] = []
_WORKFLOW_CHANNELS_FILE = Path(
  os.environ.get("WORKFLOW_CHANNELS_FILE", "/tmp/workflow_channels.json")
).resolve()

# Python 3.9 + pydantic v2 can require explicit rebuild for postponed annotations.
CompetitorVideo.model_rebuild()
CheckOriginalRequest.model_rebuild()
WarmRequest.model_rebuild()
IntegrationCheckTextRequest.model_rebuild()
TrackedChannel.model_rebuild()
TrackedChannelsRequest.model_rebuild()


def _require_cron_secret(x_cron_secret: str) -> None:
  expected = (os.environ.get("CRON_SECRET") or "").strip()
  if not expected:
    raise HTTPException(status_code=500, detail="CRON_SECRET is not configured")
  if (x_cron_secret or "").strip() != expected:
    raise HTTPException(status_code=401, detail="Invalid cron secret")


def _channel_ids_from_env() -> list[str]:
  raw = (os.environ.get("TRACKED_CHANNEL_IDS") or "").strip()
  if not raw:
    return []
  out = []
  for part in raw.split(","):
    v = part.strip()
    if v:
      out.append(v)
  return out


def _channel_ids_for_cron() -> list[str]:
  # Prefer explicitly saved workflow channels; then synced channels; then env fallback.
  workflow = _load_workflow_channels()
  ids = []
  for ch in workflow:
    cid = (ch.get("channel_id") or "").strip()
    if cid and cid not in ids:
      ids.append(cid)
  if ids:
    return ids

  ids = []
  for ch in _tracked_channels:
    cid = (ch.get("channel_id") or "").strip()
    if cid and cid not in ids:
      ids.append(cid)
  if ids:
    return ids
  return _channel_ids_from_env()


def _load_workflow_channels() -> list[dict]:
  try:
    if not _WORKFLOW_CHANNELS_FILE.exists():
      return []
    raw = json.loads(_WORKFLOW_CHANNELS_FILE.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
      return []
    out = []
    for ch in raw:
      if not isinstance(ch, dict):
        continue
      cid = str(ch.get("channel_id") or "").strip()
      if not cid:
        continue
      out.append({
        "channel_id": cid,
        "name": str(ch.get("name") or "").strip(),
        "url": str(ch.get("url") or "").strip(),
        "thumb": str(ch.get("thumb") or "").strip(),
      })
    return out
  except Exception:
    return []


def _save_workflow_channels(channels: list[dict]) -> None:
  _WORKFLOW_CHANNELS_FILE.parent.mkdir(parents=True, exist_ok=True)
  _WORKFLOW_CHANNELS_FILE.write_text(json.dumps(channels, ensure_ascii=True), encoding="utf-8")


@router.get("/health", tags=["system"])
async def health() -> dict:
  """
  Simple health check endpoint.

  Useful for uptime checks and verifying deployments.
  """
  return {"status": "ok"}


@router.put("/integration/tracked-channels", tags=["integration"])
async def set_tracked_channels(req: TrackedChannelsRequest) -> dict:
  """
  Sync tracked channels from frontend to backend.
  Cron warm job uses this list so no manual env updates are required.
  """
  global _tracked_channels
  clean = []
  seen = set()
  for ch in req.channels:
    cid = (ch.channel_id or "").strip()
    if not cid or cid in seen:
      continue
    seen.add(cid)
    clean.append({
      "channel_id": cid,
      "name": (ch.name or "").strip(),
      "url": (ch.url or "").strip(),
      "thumb": (ch.thumb or "").strip(),
    })
  _tracked_channels = clean
  return {"status": "ok", "count": len(_tracked_channels)}


@router.get("/integration/tracked-channels", tags=["integration"])
async def get_tracked_channels() -> dict:
  """Return currently synced tracked channels used by cron warmups."""
  return {"channels": list(_tracked_channels), "count": len(_tracked_channels)}


@router.put("/integration/workflow-channels", tags=["integration"])
async def set_workflow_channels(req: TrackedChannelsRequest) -> dict:
  """
  Persist shared workflow channel set used by cron warmups.
  This is independent from each user's local channel list.
  """
  clean = []
  seen = set()
  for ch in req.channels:
    cid = (ch.channel_id or "").strip()
    if not cid or cid in seen:
      continue
    seen.add(cid)
    clean.append({
      "channel_id": cid,
      "name": (ch.name or "").strip(),
      "url": (ch.url or "").strip(),
      "thumb": (ch.thumb or "").strip(),
    })
  global _tracked_channels
  _tracked_channels = list(clean)
  try:
    _save_workflow_channels(clean)
    return {"status": "ok", "count": len(clean), "persisted": True}
  except Exception:
    # Avoid blocking UI action if filesystem persistence is unavailable.
    return {"status": "ok", "count": len(clean), "persisted": False}


@router.get("/integration/workflow-channels", tags=["integration"])
async def get_workflow_channels() -> dict:
  channels = _load_workflow_channels()
  return {"channels": channels, "count": len(channels)}


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


@router.post("/cron/warm-transcripts", tags=["system"])
async def cron_warm_transcripts(
  x_cron_secret: str = Header(default=""),
  max_results: int = Query(5, ge=1, le=20),
) -> dict:
  """
  Trigger transcript warming from configured channel IDs.

  Required env vars:
  - CRON_SECRET: secret checked against X-Cron-Secret header
  - TRACKED_CHANNEL_IDS: optional fallback channel IDs if frontend has not synced yet
  """
  _require_cron_secret(x_cron_secret)

  if _warm_state.get("in_progress"):
    return {"status": "already_running", "total": _warm_state["total"], "warmed": _warm_state["warmed"], "failed": _warm_state["failed"]}

  channel_ids = _channel_ids_for_cron()
  if not channel_ids:
    raise HTTPException(
      status_code=400,
      detail="No tracked channels available. Sync channels from frontend or set TRACKED_CHANNEL_IDS.",
    )

  # Allow env override while keeping query parameter available.
  env_mr = (os.environ.get("CRON_RECENT_UPLOADS_PER_CHANNEL") or "").strip()
  if env_mr.isdigit():
    max_results = max(1, min(20, int(env_mr)))

  video_ids: list[str] = []
  seen = set()
  for channel_id in channel_ids:
    try:
      playlist_id = await asyncio.to_thread(yt.get_uploads_playlist_id, channel_id)
      items = await asyncio.to_thread(yt.get_recent_videos, playlist_id, max_results)
      for item in items:
        vid = ((item.get("snippet") or {}).get("resourceId") or {}).get("videoId")
        if not vid or vid in seen:
          continue
        seen.add(vid)
        video_ids.append(vid)
    except Exception:
      # Keep going even if one channel fails.
      continue

  to_fetch = [v for v in video_ids if v and get_transcript_cached(v) is None]
  asyncio.create_task(_run_warm_task(video_ids))
  return {
    "status": "started",
    "channels": len(channel_ids),
    "videos_found": len(video_ids),
    "to_fetch": len(to_fetch),
    "max_results_per_channel": max_results,
  }


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


@router.post("/integration/check-text", tags=["integration"])
async def integration_check_text(req: IntegrationCheckTextRequest) -> dict:
  """
  Check a provided transcript text against cached competitor transcripts.

  Intended for other tools (e.g. Trello prep flow) that already fetched a
  transcript and only need duplicate detection.
  """
  try:
    source_text = (req.transcript_text or "").strip()
    if not source_text:
      raise HTTPException(status_code=400, detail="transcript_text is required")

    translated = translate_to_german(source_text)

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
        detail="No competitor transcripts in cache. Load transcripts first.",
      )

    matches = find_matches(translated, candidates, threshold=DEFAULT_MATCH_THRESHOLD)
    for m in matches:
      m["link"] = f"https://www.youtube.com/watch?v={m['video_id']}"

    return {
      "is_duplicate": bool(matches),
      "matches": matches,
      "threshold_used": DEFAULT_MATCH_THRESHOLD,
      "translated_preview": translated[:300] + ("…" if len(translated) > 300 else ""),
      "source_video_url": req.source_video_url or "",
      "source_title": req.source_title or "",
    }
  except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
  except HTTPException:
    raise
  except Exception as e:
    raise HTTPException(status_code=502, detail=f"Integration check error: {getattr(e, 'message', str(e))}")

