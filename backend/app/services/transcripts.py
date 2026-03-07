"""
Service for fetching YouTube video transcripts.
Includes an in-memory cache to avoid hitting YouTube rate limits when
checking many US videos against the same competitor set.

To avoid using your own IP (e.g. to protect your YouTube channel):
- Run this backend on a cloud host (Railway, Render, Fly.io). All transcript
  requests then come from the server's IP.
- Or set YOUTUBE_TRANSCRIPT_PROXY to an HTTP(S) proxy URL so requests go
  through that proxy (e.g. a VPN endpoint or a paid proxy service).
"""

import os
import time
from typing import Optional

from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
    IpBlocked,
    RequestBlocked,
)

# Optional proxy: set YOUTUBE_TRANSCRIPT_PROXY (or HTTP_PROXY/HTTPS_PROXY) so
# transcript requests do not use the server's IP (e.g. when running locally
# and you don't want your business IP to hit YouTube).
def _proxy_config():
    url = os.environ.get("YOUTUBE_TRANSCRIPT_PROXY", "").strip()
    if url:
        from youtube_transcript_api.proxies import GenericProxyConfig
        return GenericProxyConfig(http_url=url, https_url=url)
    http_proxy = os.environ.get("HTTP_PROXY", os.environ.get("http_proxy", "")).strip()
    https_proxy = os.environ.get("HTTPS_PROXY", os.environ.get("https_proxy", "")).strip()
    if https_proxy or http_proxy:
        from youtube_transcript_api.proxies import GenericProxyConfig
        return GenericProxyConfig(
            http_url=https_proxy or http_proxy,
            https_url=http_proxy or https_proxy,
        )
    return None


def _make_api():
    cfg = _proxy_config()
    return YouTubeTranscriptApi(proxy_config=cfg) if cfg else YouTubeTranscriptApi()

# In-memory cache: video_id -> { "transcript", "language", "fetched_at" }
# TTL = 6 hours so re-checks don't require re-loading transcripts
_CACHE: dict[str, dict] = {}
_CACHE_TTL_SEC = 6 * 3600  # 6 hours
_MAX_CACHE_SIZE = 500


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


def get_transcript(video_id: str) -> dict:
    """
    Fetch transcript for a YouTube video.

    Args:
      video_id: The YouTube video ID (e.g. from youtube.com/watch?v=VIDEO_ID).

    Returns:
      dict with keys: transcript (str), language (str)

    Raises:
      ValueError: If transcript cannot be fetched (disabled, unavailable, etc.)
    """
    api = _make_api()
    try:
        fetched = api.fetch(video_id, languages=("en", "de"))
    except TranscriptsDisabled:
        raise ValueError("Transcripts are disabled for this video")
    except NoTranscriptFound:
        raise ValueError("No transcript found for this video")
    except VideoUnavailable:
        raise ValueError("Video is unavailable or does not exist")
    except (IpBlocked, RequestBlocked):
        raise ValueError(
            "YouTube is temporarily blocking transcript requests from this IP (too many requests). "
            "Wait a few minutes and try again, or try with fewer competitor videos."
        )

    if not fetched or len(fetched) == 0:
        raise ValueError("Transcript is empty")

    # FetchedTranscript is iterable over snippets with .text
    text = " ".join(snippet.text for snippet in fetched)
    language = fetched.language

    result = {"transcript": text, "language": language}
    _cache_set(video_id, text, language)
    return result


def cache_stats() -> dict:
    """Return cache size and list of cached video IDs for status and UI."""
    return {"cached_count": len(_CACHE), "cached_video_ids": list(_CACHE.keys())}
