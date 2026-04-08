"""
TranscriptAPI.com client (mirrors the working sibling project setup).
"""

from __future__ import annotations

import os
import logging
from typing import Optional

import httpx

_log = logging.getLogger(__name__)


def _base_url() -> str:
    return (os.environ.get("TRANSCRIPTAPI_BASE_URL") or "https://transcriptapi.com/api/v2").rstrip("/")


def _api_key() -> str:
    # Prefer the key name used in the working project; keep old name as fallback.
    key = (os.environ.get("TRANSCRIPTAPI_API_KEY") or os.environ.get("TRANSCRIPTAPI_KEY") or "").strip()
    if not key:
        raise ValueError("TRANSCRIPTAPI_API_KEY is not set")
    return key


def _request_once(video_id: str, key: str, lang: Optional[str]) -> dict:
    url = f"{_base_url()}/youtube/transcript"
    params: dict[str, str] = {
        "video_url": video_id,
        "format": "json",
        "include_timestamp": "false",
        "send_metadata": "true",
    }
    headers = {"Authorization": f"Bearer {key}"}

    with httpx.Client(timeout=30.0) as client:
        resp = client.get(url, params=params, headers=headers)
    _log.info("TranscriptAPI request: url=%s status=%s lang=%s", url, resp.status_code, lang or "auto")
    print(f"[transcripts][transcriptapi] request url={url} status={resp.status_code} lang={lang or 'auto'}")

    if resp.status_code != 200:
        return {"status": resp.status_code, "text": resp.text[:300]}

    data = resp.json()

    # Working project returns transcript segments in payload["transcript"].
    text = ""
    transcript_segments = data.get("transcript")
    if isinstance(transcript_segments, list):
        text = " ".join(
            (s.get("text") or "").strip()
            for s in transcript_segments
            if isinstance(s, dict) and s.get("text")
        ).strip()
    else:
        text = (
            (data.get("text") or "").strip()
            or (data.get("transcript") or "").strip()
            or (data.get("content") or "").strip()
        )
    language = (data.get("language") or data.get("lang") or "de").lower()

    if not text:
        return {"status": 0, "text": "empty"}

    return {"transcript": text, "language": language}


def fetch_transcript(video_id: str, lang: Optional[str] = None) -> dict:
    """
    Fetch transcript via TranscriptAPI.
    Returns dict with keys: transcript (str), language (str).
    Raises ValueError on known API errors or empty/no transcript.
    """
    key = _api_key()
    out = _request_once(video_id, key, lang)
    if "transcript" in out:
        return out

    status = out.get("status")
    if status == 401:
        raise ValueError("TranscriptAPI key invalid or missing")
    if status == 402:
        raise ValueError("TranscriptAPI: no credits left")
    if status == 404:
        raise ValueError("No transcript found for this video")
    if status == 429:
        raise ValueError("TranscriptAPI: rate limited. Wait a moment and try again")
    raise ValueError(f"TranscriptAPI error: {status} {out.get('text', '')}")

