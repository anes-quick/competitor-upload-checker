"""
Service for translating text (e.g. US transcript to German for matching).
"""

from deep_translator import GoogleTranslator


def translate_to_german(text: str) -> str:
    """
    Translate text to German. Uses Google Translate via deep-translator (no API key).

    Args:
        text: Source text (typically English).

    Returns:
        Translated German text.
    """
    if not text or not text.strip():
        return ""
    # Google Translate has a 5000 char limit per request
    max_chunk = 4500
    if len(text) <= max_chunk:
        return GoogleTranslator(source="auto", target="de").translate(text)
    chunks = [text[i : i + max_chunk] for i in range(0, len(text), max_chunk)]
    translated = [GoogleTranslator(source="auto", target="de").translate(c) for c in chunks]
    return " ".join(translated)
