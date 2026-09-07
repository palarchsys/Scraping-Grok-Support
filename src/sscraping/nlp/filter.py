"""Préfiltre O(n) avant LLM. Si aucun jeton, l'article n'est pas une agression au sens du cahier."""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import yaml

from sscraping.settings import ROOT


@lru_cache(maxsize=1)
def _patterns() -> tuple[re.Pattern[str], ...]:
    path = ROOT / "config" / "taxonomy.yaml"
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    out: list[re.Pattern[str]] = []
    for tok in raw.get("prefilter_tokens") or []:
        t = str(tok).lower().strip()
        if not t:
            continue
        if " " in t:
            out.append(re.compile(re.escape(t), re.I))
        else:
            # frontières unicode : « viol » ne matche pas « violence ».
            out.append(re.compile(rf"(?<![\w]){re.escape(t)}(?![\w])", re.I | re.UNICODE))
    return tuple(out)


def might_be_aggression(titre: str, texte: str) -> bool:
    blob = f"{titre}\n{texte}"
    return any(p.search(blob) for p in _patterns())
