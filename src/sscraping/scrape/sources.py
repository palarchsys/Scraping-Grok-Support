"""Charge config/sources.yaml. Un fichier = la liste des sites, pas du code."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(slots=True)
class Source:
    id: str
    kind: str
    listing: str
    enabled: bool
    timezone: str
    delay_s: float
    article_selectors: dict[str, str]


def load_sources(path: Path) -> list[Source]:
    raw: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8"))
    defaults = raw.get("defaults") or {}
    out: list[Source] = []
    for item in raw.get("sources") or []:
        out.append(
            Source(
                id=item["id"],
                kind=item.get("kind", "rss"),
                listing=item["listing"],
                enabled=bool(item.get("enabled", True)),
                timezone=item.get("timezone", defaults.get("timezone", "Europe/Paris")),
                delay_s=float(item.get("delay_s", defaults.get("delay_s", 0.4))),
                article_selectors=item.get("article_selectors") or {},
            )
        )
    return out
