"""Crawl HTML d'un site entier via blocs XPath (liste → pagination → article)."""

from __future__ import annotations

import logging
from urllib.parse import urljoin, urldefrag

from sscraping.scrape.base import ScrapedArticle
from sscraping.scrape.normalize import parse_date
from sscraping.scrape.sources import Source
from sscraping.scrape.xpath import first_text, parse_html, xpath_nodes

log = logging.getLogger(__name__)


def _abs(base: str, href: str) -> str | None:
    if not href or href.startswith(("javascript:", "mailto:", "#")):
        return None
    abs_url, _frag = urldefrag(urljoin(base, href.strip()))
    if not abs_url.startswith("http"):
        return None
    return abs_url


def next_page_url(html: str, current_url: str, src: Source, page_index: int) -> str | None:
    """page_index = numéro de la page *courante* (1-based)."""
    pag = src.pagination
    if pag.next:
        doc = parse_html(html)
        href = first_text(doc, pag.next)
        return _abs(current_url, href) if href else None
    if pag.page_url:
        nxt = page_index + 1
        if nxt > pag.page_start + pag.max_pages - 1:
            return None
        return pag.page_url.format(page=nxt)
    return None


def parse_listing(html: str, page_url: str, src: Source) -> list[ScrapedArticle]:
    """Extrait les cartes de la liste. titre/date optionnels (teaser) ; url obligatoire."""
    doc = parse_html(html)
    items = xpath_nodes(doc, src.listing.item) if src.listing.item else [doc]
    out: list[ScrapedArticle] = []
    seen: set[str] = set()
    for item in items:
        ctx = item if hasattr(item, "xpath") else doc
        href = first_text(ctx, src.listing.url) if src.listing.url else ""
        url = _abs(page_url, href)
        if not url or url in seen:
            continue
        seen.add(url)
        title = first_text(ctx, src.listing.title) if src.listing.title else ""
        raw_date = first_text(ctx, src.listing.date) if src.listing.date else ""
        out.append(
            ScrapedArticle(
                source=src.id,
                url=url,
                titre=title,
                texte="",
                date_publication=parse_date(raw_date, src.timezone) if raw_date else None,
            )
        )
    return out


def parse_article_page(html: str, art: ScrapedArticle, src: Source) -> ScrapedArticle:
    doc = parse_html(html)
    if src.article.title:
        title = first_text(doc, src.article.title)
        if title:
            art.titre = title
    if src.article.body:
        body = first_text(doc, src.article.body)
        if body:
            art.texte = body
    if src.article.date:
        raw = first_text(doc, src.article.date)
        dt = parse_date(raw, src.timezone) if raw else None
        if dt:
            art.date_publication = dt
    if not art.titre:
        art.titre = first_text(doc, "//h1") or art.url
    if not art.texte:
        art.texte = first_text(doc, "//article") or first_text(doc, "//main")
    return art
