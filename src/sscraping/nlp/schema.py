"""Contrat JSON étape 2. Pydantic refuse les types hors des 8 groupes."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

TypeCrime = Literal[
    "atteintes_vie",
    "violences_personnes",
    "atteintes_sexuelles",
    "atteintes_biens",
    "stupefiants",
    "criminalite_economique",
    "circulation_securite",
    "ordre_public_surete",
]

TYPE_CRIME_LABELS: dict[str, str] = {
    "atteintes_vie": "Atteintes volontaires à la vie",
    "violences_personnes": "Violences aux personnes",
    "atteintes_sexuelles": "Atteintes sexuelles",
    "atteintes_biens": "Atteintes aux biens",
    "stupefiants": "Stupéfiants",
    "criminalite_economique": "Criminalité économique et numérique",
    "circulation_securite": "Circulation et accidents",
    "ordre_public_surete": "Ordre public et sûreté",
}


class Auteur(BaseModel):
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
    is_crime: bool
    type_crime: TypeCrime | None = None
    auteur: Auteur = Field(default_factory=Auteur)
    faits: Faits = Field(default_factory=Faits)
    confidence: float = Field(ge=0.0, le=1.0)
    preuves: list[str] = Field(default_factory=list)

    @field_validator("preuves")
    @classmethod
    def clip_quotes(cls, v: list[str]) -> list[str]:
        return [s.strip()[:240] for s in v[:5] if s and s.strip()]

    @model_validator(mode="after")
    def type_si_crime(self) -> IncidentExtraction:
        if self.is_crime and self.type_crime is None:
            raise ValueError("type_crime obligatoire parmi les 8 groupes si is_crime=true")
        if not self.is_crime:
            self.type_crime = None
        return self
