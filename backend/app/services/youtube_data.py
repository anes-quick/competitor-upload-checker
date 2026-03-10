"""
YouTube Data API v3 proxy. Uses YOUTUBE_API_KEY from environment.
Used for channel resolution and fetching recent uploads (no key in frontend).
"""
from __future__ import annotations

import re
import os
from typing import Any

import httpx

_BASE = "https://www.googleapis.com/youtube/v3"


def _api_key() -> str:
    key = (os.environ.get("YOUTUBE_API_KEY") or "").strip()
    if not key:
        raise ValueError("YOUTUBE_API_KEY is not set on the server. Add it in Railway (or .env) to add channels and load videos.")
    return key


def _get(path: str, params: dict[str, Any]) -> dict:
    key = _api_key()
    params["key"] = key
    with httpx.Client(timeout=30.0) as client:
        r = client.get(f"{_BASE}{path}", params=params)
        r.raise_for_status()
        return r.json()


def resolve_channel(url: str) -> dict:
    """
    Resolve a channel URL to channel info.
    Returns dict with: channelId, name, url, thumb (optional).
    """
    handle = ""
    channel_id = ""
    handle_match = re.match(r".*@([^/?]+)", url)
    id_match = re.search(r"channel/(UC[\w-]+)", url)
    user_match = re.search(r"/user/([\w.-]+)", url)

    if id_match:
        channel_id = id_match.group(1)
    elif handle_match:
        handle = handle_match.group(1)
        try:
            import urllib.parse
            handle = urllib.parse.unquote(handle)
        except Exception:
            pass
        data = _get("/channels", {"part": "snippet", "forHandle": handle})
        if data.get("error"):
            raise ValueError(data["error"].get("message", "Channel not found"))
        items = data.get("items") or []
        if not items:
            raise ValueError("Channel not found")
        ch = items[0]
        channel_id = ch["id"]
        sn = ch.get("snippet") or {}
        return {
            "url": url,
            "handle": handle,
            "channelId": channel_id,
            "name": sn.get("title", ""),
            "thumb": (sn.get("thumbnails") or {}).get("default", {}).get("url"),
        }
    elif user_match:
        username = user_match.group(1)
        data = _get("/channels", {"part": "snippet", "forUsername": username})
        if data.get("error"):
            raise ValueError(data["error"].get("message", "Channel not found"))
        items = data.get("items") or []
        if not items:
            raise ValueError("Channel not found")
        ch = items[0]
        channel_id = ch["id"]
        sn = ch.get("snippet") or {}
        return {
            "url": url,
            "channelId": channel_id,
            "name": sn.get("title", ""),
            "thumb": (sn.get("thumbnails") or {}).get("default", {}).get("url"),
        }

    if not channel_id:
        raise ValueError("Could not parse channel URL")

    data = _get("/channels", {"part": "snippet", "id": channel_id})
    if data.get("error"):
        raise ValueError(data["error"].get("message", "Channel not found"))
    items = data.get("items") or []
    if not items:
        raise ValueError("Channel not found")
    sn = (items[0].get("snippet") or {})
    return {
        "url": url,
        "channelId": channel_id,
        "name": sn.get("title", ""),
        "thumb": (sn.get("thumbnails") or {}).get("default", {}).get("url"),
    }


def get_uploads_playlist_id(channel_id: str) -> str:
    data = _get("/channels", {"part": "contentDetails", "id": channel_id})
    if data.get("error"):
        raise ValueError(data["error"].get("message", "Channel not found"))
    items = data.get("items") or []
    if not items:
        raise ValueError("Channel not found")
    return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]


def get_recent_videos(playlist_id: str, max_results: int = 10) -> list[dict]:
    data = _get("/playlistItems", {
        "part": "snippet",
        "playlistId": playlist_id,
        "maxResults": max_results,
    })
    if data.get("error"):
        raise ValueError(data["error"].get("message", "Could not load videos"))
    return data.get("items") or []
