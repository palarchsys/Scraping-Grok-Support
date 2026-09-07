"""Diagnostic XPath hors crawl : listing + 1 article, snapshot optionnel."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import httpx
from parsel import Selector

from scraping_grok.crawler.extract import parse_article, parse_listing
from scraping_grok.scrape.base import ScrapedArticle
from scraping_grok.scrape.sources import Source
from scraping_grok.settings import ROOT

log = logging.getLogger("scraping_grok.crawler")

WALL = ("didomi", "tarteaucitron", "gdpr", "cf-challenge", "just a moment", "enable javascript")


def wall_suspect(html: str, body: str) -> bool:
    """Mur cookies / JS : gros HTML et presque pas de corps, ou bandeau consentement."""
    low = html.lower()
    marked = any(m in low for m in WALL)
    if marked and len(body) < 800:
        return True
    return len(html) > 8000 and len(body) < 300


def fetch(url: str, user_agent: str, timeout: float = 20.0) -> tuple[int, str]:
    log.info("PROBE GET %s", url)
    resp = httpx.get(
        url,
        headers={"User-Agent": user_agent, "Accept-Language": "fr-FR,fr;q=0.9"},
        follow_redirects=True,
        timeout=timeout,
    )
    log.info("PROBE status=%s url=%s bytes=%d", resp.status_code, str(resp.url), len(resp.content))
    resp.raise_for_status()
    return resp.status_code, resp.text


def probe_html(
    src: Source,
    listing_html: str,
    listing_url: str,
    article_html: str | None = None,
    article_url: str | None = None,
) -> dict[str, Any]:
    teasers = parse_listing(listing_html, listing_url, src)
    report: dict[str, Any] = {
        "source": src.id,
        "listing_url": listing_url,
        "cards": len(teasers),
        "xpath_empty": len(teasers) == 0,
        "sample": [{"url": t.url, "titre": t.titre} for t in teasers[:8]],
        "playwright_suggere": False,
    }
    sel = Selector(text=listing_html, base_url=listing_url)
    report["listing_xpath"] = {
        "item": src.listing.item,
        "item_hits": len(sel.xpath(src.listing.item)) if src.listing.item else 0,
    }
    if article_html and article_url:
        teaser = next((t for t in teasers if t.url == article_url), None) or ScrapedArticle(
            source=src.id, url=article_url, titre="", texte=""
        )
        art = parse_article(article_html, teaser, src)
        wall = wall_suspect(article_html, art.texte or "")
        report["article"] = {
            "url": art.url,
            "titre": art.titre,
            "chars": len(art.texte or ""),
            "statut": art.statut,
            "mur_cookies_ou_js": wall,
        }
        report["playwright_suggere"] = wall
        if src.article.body:
            report["article"]["body_hits"] = len(Selector(text=article_html).xpath(src.article.body))
    log.info("PROBE report %s", {k: report[k] for k in ("source", "cards", "xpath_empty", "playwright_suggere")})
    return report


def save_snapshot(source_id: str, listing_html: str, article_html: str | None) -> Path:
    dest = ROOT / "fixtures" / "html" / "probe" / source_id
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "listing.html").write_text(listing_html, encoding="utf-8")
    if article_html:
        (dest / "article.html").write_text(article_html, encoding="utf-8")
    log.info("PROBE snapshot %s", dest)
    return dest
