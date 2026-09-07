import pytest
from pydantic import ValidationError

from sscraping.nlp.schema import IncidentExtraction


def test_empty_strings_become_none() -> None:
    ext = IncidentExtraction.model_validate(
        {
            "is_crime": True,
            "type_crime": "violences_personnes",
            "auteur": {"nom": " ", "prenom": "", "nationalite": None, "age": 34, "pays_origine": ""},
            "faits": {"annee": 2025, "mois": 3, "jour": 3},
            "confidence": 0.9,
            "preuves": ["agressé à coups de poing"],
        }
    )
    assert ext.auteur.nom is None
    assert ext.auteur.prenom is None
    assert ext.auteur.age == 34


def test_invalid_age_dropped() -> None:
    ext = IncidentExtraction.model_validate(
        {
            "is_crime": True,
            "type_crime": "atteintes_vie",
            "auteur": {"age": 400},
            "faits": {},
            "confidence": 0.5,
            "preuves": [],
        }
    )
    assert ext.auteur.age is None


def test_type_crime_required_when_crime() -> None:
    with pytest.raises(ValidationError):
        IncidentExtraction.model_validate(
            {"is_crime": True, "type_crime": None, "confidence": 0.9, "preuves": []}
        )


def test_unknown_type_rejected() -> None:
    with pytest.raises(ValidationError):
        IncidentExtraction.model_validate(
            {"is_crime": True, "type_crime": "agression", "confidence": 0.9, "preuves": []}
        )


def test_non_crime_clears_type() -> None:
    ext = IncidentExtraction.model_validate(
        {"is_crime": False, "type_crime": "atteintes_biens", "confidence": 1, "preuves": []}
    )
    assert ext.type_crime is None
