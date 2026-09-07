from sscraping.nlp.pipeline import analyze_one
from sscraping.nlp.schema import IncidentExtraction


class Dummy:
    name = "dummy"
    model = "dummy"

    async def complete_json(self, system: str, user: str) -> dict:
        return {
            "is_crime": True,
            "type_crime": "violences_personnes",
            "auteur": {
                "nom": "Lefevre",
                "prenom": "Marc",
                "nationalite": "française",
                "age": 34,
                "pays_origine": None,
            },
            "faits": {"annee": 2025, "mois": 3, "jour": 3},
            "confidence": 0.91,
            "preuves": ["agressé à coups de poing"],
        }

    async def aclose(self) -> None:
        return None


class DummyLow(Dummy):
    async def complete_json(self, system: str, user: str) -> dict:
        data = await Dummy.complete_json(self, system, user)
        data["confidence"] = 0.51
        return data


async def test_budget_skipped_without_llm() -> None:
    ext, raw = await analyze_one(Dummy(), "Budget", "Les élus votent le budget", 0.7)
    assert ext.is_crime is False
    assert ext.type_crime is None
    assert raw == "{}"


async def test_crime_extracted() -> None:
    ext, _ = await analyze_one(
        Dummy(),
        "Agression à coups de poing",
        "un homme a été agressé à coups de poing",
        0.7,
    )
    assert isinstance(ext, IncidentExtraction)
    assert ext.is_crime
    assert ext.type_crime == "violences_personnes"
    assert ext.auteur.nom == "Lefevre"


async def test_low_confidence_keeps_identity() -> None:
    ext, _ = await analyze_one(
        DummyLow(),
        "Agression à coups de poing",
        "un homme a été agressé à coups de poing",
        0.7,
    )
    assert ext.is_crime
    assert ext.auteur.nom == "Lefevre"
    assert ext.auteur.prenom == "Marc"
    assert ext.confidence == 0.51
