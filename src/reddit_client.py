"""PRAW auth (read-only, app-only OAuth) + combined-subreddit fetch."""
from __future__ import annotations

import os

import praw


def make_reddit_client() -> praw.Reddit:
    """Authenticates via the client_credentials grant -- no Reddit password
    involved. PRAW negotiates this automatically when no username/password is
    passed alongside client_id/client_secret."""
    reddit = praw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        user_agent=os.environ["REDDIT_USER_AGENT"],
    )
    reddit.read_only = True
    return reddit


def fetch_new_posts(reddit: praw.Reddit, combined_subreddit: str, limit: int = 100):
    """Newest-first list of recent submissions across the combined multireddit."""
    return list(reddit.subreddit(combined_subreddit).new(limit=limit))


def fetch_new_comments(reddit: praw.Reddit, combined_subreddit: str, limit: int = 100):
    """Newest-first list of recent comments across the combined multireddit."""
    return list(reddit.subreddit(combined_subreddit).comments(limit=limit))
