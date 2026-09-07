"""Charge config/sources.yaml. Un bloc = un site à crawler, pas du code."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(slots=True)
class Pagination:
    """Navigation entre pages de liste.

    next : XPath d'un lien « page suivante » (souvent //a[@rel='next']/@href)
    page_url : gabarit optionnel « https://site/liste?page={page} »
    """

    next: str = ""
    page_url: str = ""
    page_start: int = 1
    max_pages: int = 5


@dataclass(slots=True)
class ListingXPath:
    """XPath sur la page liste : un item, son URL, éventuellement titre/date teaser."""

    item: str = ""
    url: str = ""
    title: str = ""
    date: str = ""


@dataclass(slots=True)
class ArticleXPath:
    """XPath intra-article (page complète)."""

    title: str = ""
    body: str = ""
    date: str = ""


@dataclass(slots=True)
class Source:
    """Input d'un site. kind=html (XPath, défaut) ou rss."""

    id: str
    kind: str
    listing_url: str
    enabled: bool
    timezone: str
    delay_s: float
    pagination: Pagination = field(default_factory=Pagination)
    listing: ListingXPath = field(default_factory=ListingXPath)
    article: ArticleXPath = field(default_factory=ArticleXPath)
    # alias historique (RSS + CSS)
    article_selectors: dict[str, str] = field(default_factory=dict)


def load_sources(path: Path) -> list[Source]:
    raw: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    defaults = raw.get("defaults") or {}
    default_tz = defaults.get("timezone", "Europe/Paris")
    default_delay = float(defaults.get("delay_s", 0.4))
    default_pages = int(defaults.get("max_pages", 5))
    blocks = raw.get("sites") or raw.get("sources") or []
    out: list[Source] = []
    for item in blocks:
        pag_raw = item.get("pagination") or {}
        list_raw = item.get("listing") or {}
        art_raw = item.get("article") or item.get("article_selectors") or {}
        out.append(
            Source(
                id=item["id"],
                kind=item.get("kind", "html"),
                listing_url=item.get("listing_url") or item.get("listing") or "",
                enabled=bool(item.get("enabled", True)),
                timezone=item.get("timezone", default_tz),
                delay_s=float(item.get("delay_s", default_delay)),
                pagination=Pagination(
                    next=str(pag_raw.get("next") or ""),
                    page_url=str(pag_raw.get("page_url") or ""),
                    page_start=int(pag_raw.get("page_start", 1)),
                    max_pages=int(pag_raw.get("max_pages", item.get("max_pages", default_pages))),
                ),
                listing=ListingXPath(
                    item=str(list_raw.get("item") or ""),
                    url=str(list_raw.get("url") or ""),
                    title=str(list_raw.get("title") or ""),
                    date=str(list_raw.get("date") or ""),
                ),
                article=ArticleXPath(
                    title=str(art_raw.get("title") or ""),
                    body=str(art_raw.get("body") or ""),
                    date=str(art_raw.get("date") or ""),
                ),
                article_selectors={k: str(v) for k, v in art_raw.items()} if isinstance(art_raw, dict) else {},
            )
        )
    return out
