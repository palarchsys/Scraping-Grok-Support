"""Triage d'un même fait : auteurs + date ±1 j + lieu, sinon similarité de titre."""

from __future__ import annotations

from datetime import date, timedelta
from difflib import SequenceMatcher
import unicodedata

from scraping_grok.nlp.schema import IncidentExtraction

TITLE_SIM = 0.72


def norm_name(value: str | None) -> str | None:
    if not value or not str(value).strip():
        return None
    text = unicodedata.normalize("NFD", str(value).strip())
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = text.replace("-", " ").replace("'", " ").replace("’", " ")
    text = " ".join(text.lower().split())
    return text or None


def titre_norm(value: str | None) -> str:
    return (norm_name(value) or "")[:180]


def event_date(ext: IncidentExtraction) -> date | None:
    f = ext.faits
    if f.annee is None or f.mois is None or f.jour is None:
        return None
    try:
        return date(int(f.annee), int(f.mois), int(f.jour))
    except ValueError:
        return None


def named_auteurs(ext: IncidentExtraction) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for a in [ext.auteur, *ext.auteurs]:
        nom = norm_name(a.nom)
        prenom = norm_name(a.prenom)
        if not nom or not prenom:
            continue
        key = (nom, prenom)
        if key in seen:
            continue
        seen.add(key)
        out.append(key)
    return out


def grouping_key(ext: IncidentExtraction) -> tuple[str, str, int, int, int] | None:
    """Clé exacte (premier auteur nommé + date). None si incomplet."""
    d = event_date(ext)
    people = named_auteurs(ext)
    if not d or not people:
        return None
    nom, prenom = people[0]
    return (nom, prenom, d.year, d.month, d.day)


def titles_similar(a: str, b: str, threshold: float = TITLE_SIM) -> bool:
    if not a or not b:
        return False
    return SequenceMatcher(None, a, b).ratio() >= threshold


def date_window(d: date) -> tuple[date, date]:
    return d - timedelta(days=1), d + timedelta(days=1)
