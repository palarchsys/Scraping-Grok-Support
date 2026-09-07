"""Préfiltre O(n) avant LLM. Si aucun jeton, l'article n'est pas une agression au sens du cahier."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from sscraping.settings import ROOT


@lru_cache(maxsize=1)
def _tokens() -> tuple[str, ...]:
    path = ROOT / "config" / "taxonomy.yaml"
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return tuple(t.lower() for t in raw.get("prefilter_tokens") or [])


def might_be_aggression(titre: str, texte: str) -> bool:
    blob = f"{titre}\n{texte}".lower()
    return any(tok in blob for tok in _tokens())
