"""
FetchTranscript.com API client.
Used when FETCHTRANSCRIPT_API_KEY is set for reliable transcripts without proxy/blocking.
See https://fetchtranscript.com/docs and TRANSCRIPT-RELIABILITY-RESEARCH.md.
"""

import os
from typing import Optional

import httpx

_BASE = "https://api.fetchtranscript.com/v1"

# When lang is None we try these in order so Hindi, Arabic, etc. work
_FALLBACK_LANGS = ("en", "hi", "ar", "es", "fr", "de", "pt", "ru", "ja", "ko", "zh")


def _one_request(video_id: str, key: str, lang: Optional[str]) -> dict:
    url = f"{_BASE}/transcripts/{video_id}"
    params = {"format": "text"}
    if lang:
        params["lang"] = lang
    headers = {"Authorization": f"Bearer {key}"}
    with httpx.Client(timeout=30.0) as client:
        resp = client.get(url, params=params, headers=headers)
    if resp.status_code != 200:
        return {"status": resp.status_code, "text": resp.text[:300]}
    data = resp.json()
    text = (data.get("text") or "").strip()
    language = (data.get("language") or "en").lower()
    if not text:
        return {"status": 0, "text": "empty"}
    return {"transcript": text, "language": language}


def fetch_transcript(video_id: str, lang: Optional[str] = None) -> dict:
    """
    Fetch transcript via FetchTranscript API.
    Returns dict with keys: transcript (str), language (str).
    When lang is None, tries default then several languages so Hindi, Arabic, etc. work.
    Raises ValueError on API errors or no transcript.
    """
    key = (os.environ.get("FETCHTRANSCRIPT_API_KEY") or "").strip()
    if not key:
        raise ValueError("FETCHTRANSCRIPT_API_KEY is not set")

    if lang:
        out = _one_request(video_id, key, lang)
        if "transcript" in out:
            return out
        if out.get("status") == 401:
            raise ValueError("FetchTranscript API key invalid or missing")
        if out.get("status") == 402:
            raise ValueError("FetchTranscript: no credits left. Add credits at fetchtranscript.com")
        if out.get("status") == 429:
            raise ValueError("FetchTranscript: rate limited. Wait a moment and try again")
        if out.get("status") == 404:
            raise ValueError("No transcript found for this video")
        raise ValueError(f"FetchTranscript error: {out.get('status')} {out.get('text', '')}")

    # No language specified: try without lang first, then fallback list
    to_try: list[Optional[str]] = [None] + list(_FALLBACK_LANGS)
    last_err = "No transcript found for this video"
    for try_lang in to_try:
        out = _one_request(video_id, key, try_lang)
        if "transcript" in out:
            return out
        if out.get("status") == 401:
            raise ValueError("FetchTranscript API key invalid or missing")
        if out.get("status") == 402:
            raise ValueError("FetchTranscript: no credits left. Add credits at fetchtranscript.com")
        if out.get("status") == 429:
            raise ValueError("FetchTranscript: rate limited. Wait a moment and try again")
        if out.get("status") == 404 or out.get("status") == 0:
            last_err = "No transcript found for this video"
            continue
        last_err = f"FetchTranscript error: {out.get('status')} {out.get('text', '')}"
    raise ValueError(last_err)
