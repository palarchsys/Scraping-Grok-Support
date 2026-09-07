"""Modèle d'un article scrapé (avant SQL)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class ScrapedArticle:
    source: str
    url: str
    titre: str
    texte: str
    date_publication: datetime | None
    statut: str = "ok"
    error: str | None = None
