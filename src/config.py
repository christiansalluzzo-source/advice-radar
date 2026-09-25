"""Load and validate config.

Subreddits deliberately do NOT live in config.yaml -- that file is committed
to a public repo, and the subreddit list is the one piece of this tool's
targeting that's worth keeping off a public diff. It comes from the
MONITORED_SUBREDDITS secret instead (comma-separated). Keywords stay in
config.yaml -- they're either already-public competitor names or generic
English phrases, nothing gained by hiding them, and keeping them file-based
means editing the keyword list never requires touching GitHub Secrets.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class Config:
    subreddits: list[str]
    keywords: list[str]


def load_config(path: str | Path = "config.yaml") -> Config:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Copy config.example.yaml to config.yaml and fill it in."
        )
    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    keywords = raw.get("keywords") or []
    subreddits_env = os.environ.get("MONITORED_SUBREDDITS", "")
    subreddits = [s.strip() for s in subreddits_env.split(",") if s.strip()]

    if not subreddits:
        raise ValueError(
            "MONITORED_SUBREDDITS env var is empty or unset -- nothing to monitor. "
            "Comma-separated subreddit names, e.g. 'Contractor,HVAC,Landscaping'."
        )
    if not keywords:
        raise ValueError("config.yaml has no keywords configured -- everything would match.")

    return Config(subreddits=subreddits, keywords=list(keywords))
