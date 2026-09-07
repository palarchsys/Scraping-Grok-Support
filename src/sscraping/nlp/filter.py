"""Préfiltre avant LLM. Fort = 1 hit suffit. Faible = 2 hits (moins de faux positifs)."""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Iterator

import yaml

from sscraping.settings import ROOT


def _compile(tok: str) -> re.Pattern[str]:
    t = tok.lower().strip()
    if " " in t:
        return re.compile(re.escape(t), re.I)
    return re.compile(rf"(?<![\w]){re.escape(t)}(?![\w])", re.I | re.UNICODE)


@lru_cache(maxsize=1)
def _token_sets() -> tuple[tuple[re.Pattern[str], ...], tuple[re.Pattern[str], ...]]:
    raw = yaml.safe_load((ROOT / "config" / "taxonomy.yaml").read_text(encoding="utf-8"))
    strong = tuple(_compile(t) for t in (raw.get("prefilter_strong") or []) if str(t).strip())
    weak = tuple(_compile(t) for t in (raw.get("prefilter_weak") or []) if str(t).strip())
    return strong, weak


def iter_hits(blob: str) -> Iterator[re.Match[str]]:
    strong, weak = _token_sets()
    for p in (*strong, *weak):
        m = p.search(blob)
        if m:
            yield m


def might_be_crime(titre: str, texte: str) -> bool:
    title = titre or ""
    body = f"{title}\n{texte}"
    strong, weak = _token_sets()
    if any(p.search(body) for p in strong):
        return True
    weak_hits = sum(1 for p in weak if p.search(body))
    if weak_hits >= 2:
        return True
    if any(p.search(title) for p in weak) and weak_hits >= 1:
        return True
    return False
