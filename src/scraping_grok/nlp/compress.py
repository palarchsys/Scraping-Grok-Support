"""Réduit le prompt user : lead + phrases d'identité/date/crime. Qualité d'extraction conservée."""

from __future__ import annotations

import re

from scraping_grok.scrape.normalize import clean_text

_PARA = re.compile(r"\n\s*\n")
_SENT = re.compile(r"(?<=[.!?…])\s+")
_KEEP = re.compile(
    r"""
    âgé|agee|age\b|ans\b|nommé|prénom|nationalit|pays d['’]origine|
    interpell|mis en examen|parquet|garde à vue|écrou|
    meurtre|assassinat|homicide|viol\b|poignard|tabass|braquage|cambriol|
    coup de|coups et|séquestr|enlèvement|incendie|escroquer|
    \d{1,2}\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)|
    20\d{2}
    """,
    re.I | re.VERBOSE,
)


def compress_for_llm(titre: str, texte: str, max_chars: int = 1800) -> str:
    """Titre + 2 premiers paragraphes + phrases utiles, borné max_chars."""
    body = clean_text(texte)
    paras = [p.strip() for p in _PARA.split(body) if p.strip()]
    if not paras:
        paras = [body] if body else []
    chunks: list[str] = []
    chunks.extend(paras[:2])
    extra = 0
    for para in paras[2:]:
        for sent in _SENT.split(para):
            if _KEEP.search(sent):
                chunks.append(sent.strip())
                extra += 1
                if extra >= 8:
                    break
        if extra >= 8:
            break
    merged = " ".join(c for c in chunks if c)
    if len(merged) > max_chars:
        merged = merged[:max_chars].rsplit(" ", 1)[0]
    return f"TITRE: {titre}\n\nTEXTE:\n{merged}"
