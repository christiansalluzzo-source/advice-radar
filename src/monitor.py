"""Entrypoint run by GitHub Actions on a schedule (see ../.github/workflows/monitor.yml).

One run: fetch new posts + comments across the configured subreddits, log any
keyword matches to the Leads sheet, advance the State cursors. See
../README.md and the approved plan doc for the full design rationale.
"""
from __future__ import annotations

import sys
import traceback

from config import load_config
from matcher import build_snippet, find_matches
from reddit_client import fetch_new_comments, fetch_new_posts, make_reddit_client
from sheets_client import (
    append_leads,
    ensure_leads_tab,
    ensure_state_tab,
    open_sheet,
    read_state,
    write_state,
)


def _scan_stream(items, cursor: str, text_of, row_of, keywords: list[str]):
    """Walk a newest-first list of Reddit items, stopping once we reach the
    previously-seen cursor. Returns (new_cursor, matched_rows).

    A blank cursor means "first run for this stream" -- we prime the cursor
    to the newest fullname without emitting any matches, so activating the
    monitor doesn't dump a backlog of un-vetted historical posts/comments
    into the Sheet.
    """
    if not items:
        return cursor, []

    new_cursor = items[0].fullname
    if not cursor:
        print(f"  first run for this stream -- priming cursor to {new_cursor}, no matches emitted")
        return new_cursor, []

    rows = []
    for item in items:
        if item.fullname == cursor:
            break
        text = text_of(item)
        matched = find_matches(text, keywords)
        if matched:
            rows.append(row_of(item, matched, text))
    return new_cursor, rows


def _post_row(post, matched: list[str], text: str) -> list[str]:
    from datetime import datetime, timezone

    snippet = build_snippet(text, matched[0])
    return [
        datetime.now(timezone.utc).isoformat(timespec="seconds"),
        str(post.subreddit),
        "Post",
        ", ".join(matched),
        str(post.author),
        post.title,
        snippet,
        f"https://www.reddit.com{post.permalink}",
        post.fullname,
        "",  # Category -- Christian fills in on triage
        "New",
        "",
    ]


def _comment_row(comment, matched: list[str], text: str) -> list[str]:
    from datetime import datetime, timezone

    snippet = build_snippet(text, matched[0])
    try:
        parent_title = comment.submission.title
    except Exception:
        parent_title = "(parent post unavailable)"
    return [
        datetime.now(timezone.utc).isoformat(timespec="seconds"),
        str(comment.subreddit),
        "Comment",
        ", ".join(matched),
        str(comment.author),
        parent_title,
        snippet,
        f"https://www.reddit.com{comment.permalink}",
        comment.fullname,
        "",
        "New",
        "",
    ]


def run() -> None:
    cfg = load_config()
    combined = "+".join(cfg.subreddits)
    print(f"Monitoring {len(cfg.subreddits)} subreddits, {len(cfg.keywords)} keywords.")

    reddit = make_reddit_client()
    assert reddit.read_only, "Reddit client is not read-only -- refusing to proceed"

    sheet = open_sheet()
    leads_ws = ensure_leads_tab(sheet)
    state_ws = ensure_state_tab(sheet)
    state = read_state(state_ws)

    print("Fetching new posts...")
    posts = fetch_new_posts(reddit, combined)
    new_post_cursor, post_rows = _scan_stream(
        posts,
        state.get("last_post_fullname", ""),
        text_of=lambda p: f"{p.title} {p.selftext or ''}",
        row_of=_post_row,
        keywords=cfg.keywords,
    )

    print("Fetching new comments...")
    comments = fetch_new_comments(reddit, combined)
    new_comment_cursor, comment_rows = _scan_stream(
        comments,
        state.get("last_comment_fullname", ""),
        text_of=lambda c: c.body or "",
        row_of=_comment_row,
        keywords=cfg.keywords,
    )

    all_rows = post_rows + comment_rows
    print(f"Matched {len(post_rows)} post(s), {len(comment_rows)} comment(s).")
    append_leads(leads_ws, all_rows)

    write_state(state_ws, new_post_cursor, new_comment_cursor, status="ok")
    print("Done.")


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:  # noqa: BLE001 -- top-level guard, see plan step 11
        traceback.print_exc()
        try:
            # Best-effort: only works if Sheets auth already succeeded.
            sheet = open_sheet()
            state_ws = ensure_state_tab(sheet)
            existing = read_state(state_ws)
            write_state(
                state_ws,
                existing.get("last_post_fullname", ""),
                existing.get("last_comment_fullname", ""),
                status=f"error: {exc}",
            )
        except Exception:
            pass  # Sheets itself was unreachable -- nothing more we can log there.
        sys.exit(1)
