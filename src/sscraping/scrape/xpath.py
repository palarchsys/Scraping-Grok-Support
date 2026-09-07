"""Évaluation XPath sur HTML (lxml).

Pourquoi XPath plutôt que CSS pour le crawl site : un seul langage pour
attributs (@href, @datetime), axes (following), et contextes d'item (.).
"""

from __future__ import annotations

from lxml import html as lhtml
from lxml.etree import _Element

from sscraping.scrape.normalize import clean_text


def parse_html(document: str) -> lhtml.HtmlElement:
    # Unicode in → pas de re-décodage (sinon latin-1 et mojibake).
    parser = lhtml.HTMLParser(encoding="utf-8", recover=True)
    return lhtml.fromstring(document.encode("utf-8"), parser=parser)


def xpath_nodes(root: _Element, expr: str) -> list[object]:
    if not expr or not expr.strip():
        return []
    try:
        found = root.xpath(expr)
    except Exception:  # noqa: BLE001 — XPath cassé = pas de match, on loggue ailleurs
        return []
    if found is None:
        return []
    if isinstance(found, (str, bytes, int, float)):
        return [found]
    return list(found)


def node_text(node: object) -> str:
    if node is None:
        return ""
    if isinstance(node, (bytes, bytearray)):
        return node.decode("utf-8", errors="replace").strip()
    if isinstance(node, (int, float)):
        return str(node)
    if isinstance(node, str):
        return node.strip()
    if isinstance(node, _Element):
        for junk in node.xpath(".//script|.//style|.//noscript"):
            parent = junk.getparent()
            if parent is not None:
                parent.remove(junk)
        return clean_text(" ".join(node.itertext()))
    return clean_text(str(node))


def first_text(root: _Element, expr: str) -> str:
    for n in xpath_nodes(root, expr):
        t = node_text(n)
        if t:
            return t
    return ""


def first_attr_or_text(root: _Element, expr: str) -> str:
    """@href / @datetime / texte d'élément — le XPath décide."""
    return first_text(root, expr)
