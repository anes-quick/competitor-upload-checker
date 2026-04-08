"""
TranscriptAPI.com client.
Primary provider when TRANSCRIPTAPI_KEY is set.
"""

from __future__ import annotations

import os
import logging
from typing import Optional

import httpx

_log = logging.getLogger(__name__)


def _base_url() -> str:
    # Keep configurable in case provider path changes.
    return (os.environ.get("TRANSCRIPTAPI_BASE_URL") or "https://api.transcriptapi.com/v1").rstrip("/")


def _api_key() -> str:
    key = (os.environ.get("TRANSCRIPTAPI_KEY") or "").strip()
    if not key:
        raise ValueError("TRANSCRIPTAPI_KEY is not set")
    return key


def _request_once(video_id: str, key: str, lang: Optional[str]) -> dict:
    url = f"{_base_url()}/transcripts/{video_id}"
    params: dict[str, str] = {}
    if lang:
        params["lang"] = lang

    # Try both common auth styles.
    headers = {
        "Authorization": f"Bearer {key}",
        "x-api-key": key,
    }

    with httpx.Client(timeout=30.0) as client:
        resp = client.get(url, params=params, headers=headers)
    _log.info("TranscriptAPI request: url=%s status=%s lang=%s", url, resp.status_code, lang or "auto")

    if resp.status_code != 200:
        return {"status": resp.status_code, "text": resp.text[:300]}

    data = resp.json()

    # Accept a few common payload styles.
    text = (
        (data.get("text") or "").strip()
        or (data.get("transcript") or "").strip()
        or (data.get("content") or "").strip()
    )
    language = (data.get("language") or data.get("lang") or "en").lower()

    # Segment array -> text fallback
    if not text and isinstance(data.get("segments"), list):
        text = " ".join((s.get("text") or "").strip() for s in data["segments"] if isinstance(s, dict)).strip()

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

