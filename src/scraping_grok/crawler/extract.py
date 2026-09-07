"""XPath via parsel (le sélecteur de Scrapy). Isolé pour tests hors réseau."""

from __future__ import annotations

import logging
from urllib.parse import urldefrag, urljoin

from parsel import Selector

from scraping_grok.scrape.base import ScrapedArticle
from scraping_grok.scrape.normalize import clean_text, parse_date
from scraping_grok.scrape.sources import Source

log = logging.getLogger("scraping_grok.crawler")


def abs_url(base: str, href: str | None) -> str | None:
    if not href:
        return None
    href = href.strip()
    if not href or href.startswith(("javascript:", "mailto:", "#")):
        return None
    abs_, _frag = urldefrag(urljoin(base, href))
    if not abs_.startswith("http"):
        return None
    return abs_


def xpath_text(sel: Selector, expr: str, *, where: str = "") -> str:
    if not expr:
        return ""
    nodes = sel.xpath(expr)
    log.debug("xpath %s expr=%r matches=%d", where, expr, len(nodes))
    if not nodes:
        return ""
    text = nodes.xpath("string(.)").get()
    if text and text.strip():
        return clean_text(text)
    raw = nodes.get()
    return clean_text(raw or "")


def parse_listing(html: str, page_url: str, src: Source) -> list[ScrapedArticle]:
    sel = Selector(text=html, base_url=page_url)
    xp_item = src.listing.item or "."
    cards = sel.xpath(xp_item)
    log.info("listing url=%s xpath.item=%r cards=%d", page_url, xp_item, len(cards))
    if not cards:
        log.warning("XPATH VIDE listing.item=%s url=%s snippet=%r", xp_item, page_url, html[:400])
    out: list[ScrapedArticle] = []
    seen: set[str] = set()
    for i, card in enumerate(cards):
        href = xpath_text(card, src.listing.url, where=f"listing[{i}].url")
        url = abs_url(page_url, href)
        if not url:
            log.debug("listing[%d] sans url href=%r", i, href)
            continue
        if url in seen:
            log.debug("listing[%d] doublon %s", i, url)
            continue
        seen.add(url)
        title = xpath_text(card, src.listing.title, where=f"listing[{i}].title") if src.listing.title else ""
        raw_date = xpath_text(card, src.listing.date, where=f"listing[{i}].date") if src.listing.date else ""
        log.debug("listing[%d] url=%s titre=%r date=%r", i, url, title[:80], raw_date)
        out.append(
            ScrapedArticle(
                source=src.id,
                url=url,
                titre=title,
                texte="",
                date_publication=parse_date(raw_date, src.timezone) if raw_date else None,
            )
        )
    log.info("listing url=%s extraits=%d uniques", page_url, len(out))
    return out


def next_page_url(html: str, current_url: str, src: Source, page_index: int) -> str | None:
    pag = src.pagination
    if pag.next:
        sel = Selector(text=html, base_url=current_url)
        href = xpath_text(sel, pag.next, where="pagination.next")
        url = abs_url(current_url, href) if href else None
        log.info("pagination.next page=%d href=%r abs=%s", page_index, href, url)
        return url
    if pag.page_url:
        nxt = page_index + 1
        if nxt > pag.page_start + pag.max_pages - 1:
            log.info("pagination.page_url plafond atteint page=%d", page_index)
            return None
        url = pag.page_url.format(page=nxt)
        log.info("pagination.page_url page=%d -> %s", nxt, url)
        return url
    log.debug("pas de pagination configurée")
    return None


def parse_article(html: str, art: ScrapedArticle, src: Source) -> ScrapedArticle:
    sel = Selector(text=html)
    log.debug("article parse url=%s html_chars=%d", art.url, len(html))
    if src.article.title:
        title = xpath_text(sel, src.article.title, where="article.title")
        if title:
            art.titre = title
        else:
            log.warning("XPATH VIDE article.title=%s url=%s", src.article.title, art.url)
    if src.article.body:
        body = xpath_text(sel, src.article.body, where="article.body")
        if body:
            art.texte = body
        else:
            log.warning("XPATH VIDE article.body=%s url=%s", src.article.body, art.url)
    if src.article.date:
        raw = xpath_text(sel, src.article.date, where="article.date")
        dt = parse_date(raw, src.timezone) if raw else None
        if dt:
            art.date_publication = dt
        else:
            log.debug("date article absente ou illisible raw=%r", raw)
    if not art.titre:
        art.titre = xpath_text(sel, "//h1", where="fallback.h1") or art.url
    if not art.texte:
        art.texte = xpath_text(sel, "//article", where="fallback.article") or xpath_text(
            sel, "//main", where="fallback.main"
        )
    if not art.texte:
        log.warning("corps vide url=%s", art.url)
        art.statut = "erreur"
        art.error = "xpath article vide"
    log.info("article ok url=%s titre=%r chars=%d", art.url, art.titre[:80], len(art.texte or ""))
    return art
