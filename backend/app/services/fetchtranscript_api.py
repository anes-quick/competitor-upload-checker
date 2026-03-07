"""
FetchTranscript.com API client.
Used when FETCHTRANSCRIPT_API_KEY is set for reliable transcripts without proxy/blocking.
See https://fetchtranscript.com/docs and TRANSCRIPT-RELIABILITY-RESEARCH.md.
"""

import os
from typing import Optional

import httpx

_BASE = "https://api.fetchtranscript.com/v1"


def fetch_transcript(video_id: str, lang: Optional[str] = None) -> dict:
    """
    Fetch transcript via FetchTranscript API.
    Returns dict with keys: transcript (str), language (str).
    Raises ValueError on API errors or no transcript.
    """
    key = (os.environ.get("FETCHTRANSCRIPT_API_KEY") or "").strip()
    if not key:
        raise ValueError("FETCHTRANSCRIPT_API_KEY is not set")

    url = f"{_BASE}/transcripts/{video_id}"
    params = {"format": "text"}
    if lang:
        params["lang"] = lang
    headers = {"Authorization": f"Bearer {key}"}

    with httpx.Client(timeout=30.0) as client:
        resp = client.get(url, params=params, headers=headers)

    if resp.status_code == 401:
        raise ValueError("FetchTranscript API key invalid or missing")
    if resp.status_code == 402:
        raise ValueError("FetchTranscript: no credits left. Add credits at fetchtranscript.com")
    if resp.status_code == 429:
        raise ValueError("FetchTranscript: rate limited. Wait a moment and try again")
    if resp.status_code == 404:
        raise ValueError("No transcript found for this video")
    if resp.status_code != 200:
        raise ValueError(f"FetchTranscript error: {resp.status_code} {resp.text[:200]}")

    data = resp.json()
    text = (data.get("text") or "").strip()
    language = (data.get("language") or "en").lower()

    if not text:
        raise ValueError("Transcript is empty")

    return {"transcript": text, "language": language}
