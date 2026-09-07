"""Enrichissement du corps via HTML article. selectolax = CSS rapide (modest HTML)."""

from __future__ import annotations

from selectolax.parser import HTMLParser

from sscraping.scrape.normalize import clean_text


def extract_article(html: str, selectors: dict[str, str]) -> tuple[str, str]:
    tree = HTMLParser(html)
    title = _first_text(tree, selectors.get("title", "h1"))
    if not title:
        og = tree.css_first('meta[property="og:title"]')
        if og:
            title = og.attributes.get("content") or ""
    body_sel = selectors.get("body", "article")
    body = _body_text(tree, body_sel)
    if not body:
        body = _body_text(tree, "article") or _body_text(tree, "main")
    return clean_text(title), clean_text(body)


def _body_text(tree: HTMLParser, selector: str) -> str:
    body_node = tree.css_first(selector)
    if not body_node:
        return ""
    for junk in body_node.css("script, style, nav, aside, figure, iframe, form"):
        junk.decompose()
    return body_node.text(separator=" ", strip=True)


def _first_text(tree: HTMLParser, selector: str) -> str:
    node = tree.css_first(selector)
    return node.text(strip=True) if node else ""
