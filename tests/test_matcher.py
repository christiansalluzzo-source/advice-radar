"""No-network unit test for matcher.py."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from matcher import build_snippet, find_matches  # noqa: E402


def test_find_matches_case_insensitive():
    assert find_matches("Switching from Jobber, any advice?", ["Jobber"]) == ["Jobber"]
    assert find_matches("switching FROM jobber", ["Jobber"]) == ["Jobber"]


def test_find_matches_multiple_keywords_one_row():
    text = "Tired of paying for Jobber, looking for an alternative to it"
    matched = find_matches(text, ["Jobber", "tired of paying for", "alternative to"])
    assert matched == ["Jobber", "tired of paying for", "alternative to"]


def test_find_matches_no_match():
    assert find_matches("Just posting about my lawn mower", ["Jobber", "Spotio"]) == []


def test_find_matches_empty_inputs():
    assert find_matches("", ["Jobber"]) == []
    assert find_matches("Jobber is great", []) == []


def test_build_snippet_centers_on_keyword():
    text = "a" * 150 + "Jobber" + "b" * 150
    snippet = build_snippet(text, "Jobber", radius=20)
    assert "Jobber" in snippet
    assert snippet.startswith("…")
    assert snippet.endswith("…")
    assert len(snippet) < len(text)


def test_build_snippet_short_text_no_ellipsis():
    text = "Jobber is too expensive"
    snippet = build_snippet(text, "Jobber", radius=100)
    assert snippet == text
