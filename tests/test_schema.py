from sscraping.nlp.schema import IncidentExtraction


def test_empty_strings_become_none() -> None:
    ext = IncidentExtraction.model_validate(
        {
            "is_aggression": True,
            "categorie": "violence_physique",
            "agresseur": {"nom": " ", "prenom": "", "nationalite": None, "age": 34, "pays_origine": ""},
            "faits": {"annee": 2025, "mois": 3, "jour": 3},
            "confidence": 0.9,
            "preuves": ["agressé à coups de poing"],
        }
    )
    assert ext.agresseur.nom is None
    assert ext.agresseur.prenom is None
    assert ext.agresseur.age == 34


def test_invalid_age_dropped() -> None:
    ext = IncidentExtraction.model_validate(
        {
            "is_aggression": True,
            "categorie": "homicide",
            "agresseur": {"age": 400},
            "faits": {},
            "confidence": 0.5,
            "preuves": [],
        }
    )
    assert ext.agresseur.age is None
