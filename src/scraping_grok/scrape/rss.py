"""Parseur RSS/Atom via lxml — plus prévisible que feedparser pour un cours HTTP/XML."""

from __future__ import annotations

import re

from lxml import etree

from scraping_grok.scrape.base import ScrapedArticle
from scraping_grok.scrape.normalize import clean_text, parse_date

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "dc": "http://purl.org/dc/elements/1.1/",
    "content": "http://purl.org/rss/1.0/modules/content/",
}

# lxml refuse une déclaration d'encodage sur une str Unicode.
_XML_DECL = re.compile(r"^<\?xml[^?]*\?>", re.I)


def parse_feed(xml: str, source_id: str, timezone_name: str) -> list[ScrapedArticle]:
    payload = _XML_DECL.sub("", xml.lstrip(), count=1)
    parser = etree.XMLParser(recover=True, resolve_entities=False, no_network=True)
    root = etree.fromstring(payload.encode("utf-8", errors="replace"), parser)
    items = root.findall(".//item")
    if not items:
        items = root.findall(".//{http://www.w3.org/2005/Atom}entry")
        if not items:
            items = root.findall(".//atom:entry", NS)
    out: list[ScrapedArticle] = []
    for item in items:
        title = _child_text(item, "title") or _child_text(item, "atom:title")
        link = _link(item)
        raw_date = (
            _child_text(item, "pubDate")
            or _child_text(item, "dc:date")
            or _child_text(item, "atom:updated")
            or _child_text(item, "atom:published")
        )
        summary = (
            _child_text(item, "content:encoded")
            or _child_text(item, "description")
            or _child_text(item, "atom:summary")
            or _child_text(item, "atom:content")
        )
        if not title or not link:
            continue
        out.append(
            ScrapedArticle(
                source=source_id,
                url=link,
                titre=clean_text(title),
                texte=clean_text(_strip_html(summary)),
                date_publication=parse_date(raw_date, timezone_name),
            )
        )
    return out


def _child_text(el: etree._Element, name: str) -> str | None:
    if ":" in name:
        node = el.find(name, NS)
        if node is None:
            local = name.split(":", 1)[1]
            node = el.find(f"{{*}}{local}")
    else:
        node = el.find(name)
        if node is None:
            node = el.find(f"{{*}}{name}")
    if node is None:
        return None
    text = (node.text or "") + "".join(etree.tostring(c, encoding="unicode") for c in node)
    return text or None


def _link(el: etree._Element) -> str | None:
    link = el.find("link")
    if link is None:
        link = el.find("{*}link")
    if link is not None and (link.text or "").strip():
        return link.text.strip()
    if link is not None:
        href = link.get("href")
        if href:
            return href.strip()
    atom_link = el.find("atom:link", NS)
    if atom_link is None:
        atom_link = el.find("{http://www.w3.org/2005/Atom}link")
    if atom_link is not None:
        href = atom_link.get("href")
        if href:
            return href.strip()
    guid = el.find("guid")
    if guid is None:
        guid = el.find("{*}guid")
    if guid is not None and (guid.text or "").startswith("http"):
        return guid.text.strip()
    return None


def _strip_html(blob: str | None) -> str:
    if not blob:
        return ""
    if "<" not in blob:
        return blob
    try:
        doc = etree.HTML(blob)
        return " ".join(doc.itertext()) if doc is not None else blob
    except etree.ParserError:
        return blob
