"""Contrat JSON étape 2. Pydantic refuse les labels hors taxonomie et les âges absurdes."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

Categorie = Literal[
    "non_agression",
    "violence_physique",
    "agression_sexuelle",
    "homicide",
    "tentative",
    "menace",
    "vol_avec_violence",
    "autre_agression",
]


class Agresseur(BaseModel):
    nom: str | None = None
    prenom: str | None = None
    nationalite: str | None = None
    age: int | None = None
    pays_origine: str | None = None

    @field_validator("nom", "prenom", "nationalite", "pays_origine", mode="before")
    @classmethod
    def empty_to_none(cls, v: object) -> object:
        if v is None:
            return None
        if isinstance(v, str) and not v.strip():
            return None
        return v

    @field_validator("age")
    @classmethod
    def age_range(cls, v: int | None) -> int | None:
        if v is None:
            return None
        if v < 1 or v > 120:
            return None
        return v


class Faits(BaseModel):
    annee: int | None = None
    mois: int | None = None
    jour: int | None = None

    @field_validator("mois")
    @classmethod
    def mois_ok(cls, v: int | None) -> int | None:
        if v is None:
            return None
        return v if 1 <= v <= 12 else None

    @field_validator("jour")
    @classmethod
    def jour_ok(cls, v: int | None) -> int | None:
        if v is None:
            return None
        return v if 1 <= v <= 31 else None


class IncidentExtraction(BaseModel):
    is_aggression: bool
    categorie: Categorie
    agresseur: Agresseur = Field(default_factory=Agresseur)
    faits: Faits = Field(default_factory=Faits)
    confidence: float = Field(ge=0.0, le=1.0)
    preuves: list[str] = Field(default_factory=list)

    @field_validator("preuves")
    @classmethod
    def clip_quotes(cls, v: list[str]) -> list[str]:
        return [s.strip()[:240] for s in v[:5] if s and s.strip()]
