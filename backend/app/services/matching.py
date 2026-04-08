"""
Service for fuzzy topic matching between transcripts.
"""

from __future__ import annotations

import re
import unicodedata

# Common stopwords (German + English) to reduce noise
STOPWORDS = {
    "der", "die", "das", "und", "ist", "in", "zu", "den", "von", "mit", "auf",
    "für", "sich", "nicht", "auch", "bei", "es", "ein", "eine", "einer", "eines",
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of",
    "with", "by", "from", "as", "is", "was", "are", "were", "been", "be",
    "have", "has", "had", "do", "does", "did", "will", "would", "could", "should",
    "it", "its", "this", "that", "these", "those", "i", "you", "he", "she", "we", "they",
}

DEFAULT_MATCH_THRESHOLD = 0.17


def _normalize(text: str) -> set[str]:
    """Lowercase, remove punctuation/numbers, split into words, drop stopwords."""
    text = text.lower().strip()
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\d+", " ", text)
    words = set(w for w in text.split() if len(w) > 1 and w not in STOPWORDS)
    return words


def similarity(a: str, b: str) -> float:
    """
    Jaccard-like similarity between two texts (word overlap).

    Returns a value between 0 and 1.
    """
    wa = _normalize(a)
    wb = _normalize(b)
    if not wa or not wb:
        return 0.0
    intersection = len(wa & wb)
    union = len(wa | wb)
    return intersection / union if union else 0.0


def find_matches(
    source_text: str,
    candidates: list[dict],
    threshold: float = DEFAULT_MATCH_THRESHOLD,
) -> list[dict]:
    """
    Find competitor videos whose transcript is similar to the source (translated US).

    Args:
        source_text: Translated US transcript (German).
        candidates: List of {"video_id", "transcript", "channel_name", "title", ...}.
        threshold: Minimum similarity score (0–1) to count as match.

    Returns:
        List of matches sorted by score descending, each with score added.
    """
    matches = []
    for c in candidates:
        transcript = c.get("transcript") or ""
        if not transcript.strip():
            continue
        score = similarity(source_text, transcript)
        if score >= threshold:
            m = dict(c)
            m["score"] = round(score, 3)
            matches.append(m)
    matches.sort(key=lambda x: x["score"], reverse=True)
    return matches
