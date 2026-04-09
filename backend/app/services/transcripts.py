"""
Service for fetching YouTube video transcripts.
Includes an in-memory cache to avoid hitting YouTube rate limits when
checking many US videos against the same competitor set.

Provider order:
1) TranscriptAPI (TRANSCRIPTAPI_API_KEY)
2) FetchTranscript (FETCHTRANSCRIPT_API_KEY)
"""

import os
import time
import logging
from typing import Optional

# In-memory cache: video_id -> { "transcript", "language", "fetched_at" }
# TTL = 4 days so re-checks don't require re-loading transcripts
_CACHE: dict[str, dict] = {}
_CACHE_TTL_SEC = 4 * 24 * 3600  # 4 days
_MAX_CACHE_SIZE = 500
_log = logging.getLogger(__name__)

PROVIDER_TRANSCRIPTAPI = "transcriptapi"
PROVIDER_FETCHTRANSCRIPT = "fetchtranscript"


def _normalize_provider(value: str, default: str) -> str:
    v = (value or "").strip().lower()
    if v in (PROVIDER_TRANSCRIPTAPI, PROVIDER_FETCHTRANSCRIPT):
        return v
    return default


def _provider_order() -> list[str]:
    primary = _normalize_provider(
        os.environ.get("TRANSCRIPT_PROVIDER_PRIMARY", ""),
        PROVIDER_TRANSCRIPTAPI,
    )
    fallback = _normalize_provider(
        os.environ.get("TRANSCRIPT_PROVIDER_FALLBACK", ""),
        PROVIDER_FETCHTRANSCRIPT,
    )
    order = [primary]
    if fallback != primary:
        order.append(fallback)
    return order


def _cache_get(video_id: str) -> Optional[dict]:
    now = time.time()
    if video_id not in _CACHE:
        return None
    entry = _CACHE[video_id]
    if now - entry["fetched_at"] > _CACHE_TTL_SEC:
        del _CACHE[video_id]
        return None
    return {"transcript": entry["transcript"], "language": entry["language"]}


def _cache_set(video_id: str, transcript: str, language: str) -> None:
    if len(_CACHE) >= _MAX_CACHE_SIZE:
        # Evict oldest
        oldest_id = min(_CACHE, key=lambda k: _CACHE[k]["fetched_at"])
        del _CACHE[oldest_id]
    _CACHE[video_id] = {
        "transcript": transcript,
        "language": language,
        "fetched_at": time.time(),
    }


def get_transcript_cached(video_id: str) -> Optional[dict]:
    """Return transcript from cache if present and not expired. Does not fetch."""
    return _cache_get(video_id)


def _get_transcript_via_fetchtranscript(video_id: str, preferred_lang: Optional[str] = None) -> dict:
    """Use FetchTranscript.com API when key is set. Raises ValueError on error."""
    from app.services.fetchtranscript_api import fetch_transcript as ft_fetch
    return ft_fetch(video_id, lang=preferred_lang)

def _get_transcript_via_transcriptapi(video_id: str, preferred_lang: Optional[str] = None) -> dict:
    """Use TranscriptAPI.com when key is set. Raises ValueError on error."""
    from app.services.transcriptapi_client import fetch_transcript as ta_fetch
    return ta_fetch(video_id, lang=preferred_lang)


def get_transcript(video_id: str, preferred_lang: Optional[str] = None) -> dict:
    """
    Fetch transcript for a YouTube video.
    Provider order (configurable):
      - TRANSCRIPT_PROVIDER_PRIMARY (default: transcriptapi)
      - TRANSCRIPT_PROVIDER_FALLBACK (default: fetchtranscript)
      - No direct YouTube fallback; uses API providers only

    preferred_lang: optional "en" or "de" to prefer that language; omit for any language (e.g. Hindi, Arabic).

    Returns:
      dict with keys: transcript (str), language (str)

    Raises:
      ValueError: If transcript cannot be fetched (disabled, unavailable, etc.)
    """
    has_ta = (os.environ.get("TRANSCRIPTAPI_API_KEY") or os.environ.get("TRANSCRIPTAPI_KEY") or "").strip()
    has_ft = (os.environ.get("FETCHTRANSCRIPT_API_KEY") or "").strip()
    _log.info(
        "Transcript provider selection: video_id=%s has_transcriptapi=%s has_fetchtranscript=%s preferred_lang=%s",
        video_id,
        bool(has_ta),
        bool(has_ft),
        preferred_lang or "auto",
    )
    print(
        f"[transcripts] select video_id={video_id} has_transcriptapi={bool(has_ta)} "
        f"has_fetchtranscript={bool(has_ft)} preferred_lang={preferred_lang or 'auto'}"
    )

    result = None
    errors: list[str] = []
    for provider in _provider_order():
        try:
            if provider == PROVIDER_TRANSCRIPTAPI:
                if not has_ta:
                    errors.append("transcriptapi: key not set")
                    continue
                result = _get_transcript_via_transcriptapi(video_id, preferred_lang)
                _log.info("Transcript provider used: transcriptapi")
                print("[transcripts] provider=transcriptapi")
                break
            if provider == PROVIDER_FETCHTRANSCRIPT:
                if not has_ft:
                    errors.append("fetchtranscript: key not set")
                    continue
                result = _get_transcript_via_fetchtranscript(video_id, preferred_lang)
                _log.info("Transcript provider used: fetchtranscript")
                print("[transcripts] provider=fetchtranscript")
                break
        except Exception as e:
            msg = str(e)[:220]
            errors.append(f"{provider}: {msg}")
            print(f"[transcripts] {provider}_failed reason={msg}")
            continue

    if result is None:
        raise ValueError("All transcript providers failed: " + " | ".join(errors))

    text = result["transcript"]
    language = result["language"]
    _cache_set(video_id, text, language)
    return {"transcript": text, "language": language}


def cache_stats() -> dict:
    """Return cache size and list of cached video IDs for status and UI."""
    return {"cached_count": len(_CACHE), "cached_video_ids": list(_CACHE.keys())}
