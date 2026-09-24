"""Pure keyword-matching logic. No network calls -- unit-testable in isolation."""
from __future__ import annotations


def find_matches(text: str, keywords: list[str]) -> list[str]:
    """Return the subset of `keywords` that appear in `text` (case-insensitive
    substring match). Order of the input list is preserved; no duplicates."""
    if not text or not keywords:
        return []
    haystack = text.lower()
    return [kw for kw in keywords if kw.lower() in haystack]


def build_snippet(text: str, keyword: str, radius: int = 100) -> str:
    """~200-char excerpt centered on the first occurrence of `keyword` in `text`.
    Falls back to a plain head-truncation if the keyword can't be located
    (shouldn't happen given find_matches already confirmed a match, but this
    keeps the function safe to call standalone)."""
    if not text:
        return ""
    lower_text = text.lower()
    idx = lower_text.find(keyword.lower())
    if idx == -1:
        return text[: radius * 2].strip()
    start = max(0, idx - radius)
    end = min(len(text), idx + len(keyword) + radius)
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(text) else ""
    return f"{prefix}{text[start:end].strip()}{suffix}"
