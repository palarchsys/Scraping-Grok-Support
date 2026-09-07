"""Triage : un fait = même date + même nom + même prénom (auteur), normalisés."""

from __future__ import annotations

import unicodedata

from scraping_grok.nlp.schema import IncidentExtraction


def norm_name(value: str | None) -> str | None:
    if not value or not str(value).strip():
        return None
    text = unicodedata.normalize("NFD", str(value).strip())
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = text.replace("-", " ").replace("'", " ").replace("’", " ")
    text = " ".join(text.lower().split())
    return text or None


def grouping_key(ext: IncidentExtraction) -> tuple[str, str, int, int, int] | None:
    """None si on ne peut pas dédoublonner sans coller des faits distincts."""
    nom = norm_name(ext.auteur.nom)
    prenom = norm_name(ext.auteur.prenom)
    f = ext.faits
    if not nom or not prenom or f.annee is None or f.mois is None or f.jour is None:
        return None
    return (nom, prenom, f.annee, f.mois, f.jour)
