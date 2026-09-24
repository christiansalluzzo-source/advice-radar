"""Load and validate config.yaml."""
from __future__ import annotations

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

    subreddits = raw.get("subreddits") or []
    keywords = raw.get("keywords") or []

    if not subreddits:
        raise ValueError("config.yaml has no subreddits configured -- nothing to monitor.")
    if not keywords:
        raise ValueError("config.yaml has no keywords configured -- everything would match.")

    return Config(subreddits=list(subreddits), keywords=list(keywords))
