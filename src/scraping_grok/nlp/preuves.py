"""Citations locales — pas générées par le LLM (économie de tokens + pas d'hallucination)."""

from __future__ import annotations

import re

from scraping_grok.nlp.filter import iter_hits

_SENT = re.compile(r"(?<=[.!?…])\s+")


def local_preuves(titre: str, texte: str, limit: int = 3, max_len: int = 120) -> list[str]:
    blob = f"{titre}. {texte}"
    out: list[str] = []
    seen: set[str] = set()
    for sent in _SENT.split(blob):
        s = " ".join(sent.split())
        if len(s) < 12:
            continue
        if not any(True for _ in iter_hits(s)):
            continue
        key = s.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(s[:max_len])
        if len(out) >= limit:
            break
    return out
