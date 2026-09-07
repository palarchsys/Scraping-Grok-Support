from scraping_grok.nlp.pipeline import analyze_one
from scraping_grok.nlp.schema import IncidentExtraction


class Dummy:
    name = "dummy"
    model = "dummy"
    usage = {"prompt_tokens": 0, "completion_tokens": 0, "calls": 0}

    async def complete_json(self, system: str, user: str) -> dict:
        return {
            "is_crime": True,
            "type_crime": "violences_personnes",
            "auteurs": [
                {
                    "nom": "Lefevre",
                    "prenom": "Marc",
                    "nationalite": "française",
                    "age": 34,
                    "pays_origine": None,
                }
            ],
            "lieu": "Clairville",
            "faits": {"annee": 2025, "mois": 3, "jour": 3},
            "confidence": 0.91,
        }

    async def aclose(self) -> None:
        return None


class DummyLow(Dummy):
    async def complete_json(self, system: str, user: str) -> dict:
        data = await Dummy.complete_json(self, system, user)
        data["confidence"] = 0.51
        return data


class DummyBadThenOk(Dummy):
    def __init__(self) -> None:
        self.n = 0

    async def complete_json(self, system: str, user: str) -> dict:
        self.n += 1
        if self.n == 1:
            return {"is_crime": True}
        return await Dummy.complete_json(self, system, user)


async def test_budget_skipped_without_llm() -> None:
    ext, raw, status = await analyze_one(Dummy(), "Budget", "Les élus votent le budget", 0.7)
    assert ext.is_crime is False
    assert status == "ignored"
    assert raw == "{}"


async def test_crime_extracted() -> None:
    ext, _, status = await analyze_one(
        Dummy(),
        "Agression à coups de poing",
        "un homme a été agressé à coups de poing",
        0.7,
    )
    assert isinstance(ext, IncidentExtraction)
    assert status == "extracted"
    assert ext.is_crime
    assert ext.auteur.nom == "Lefevre"
    assert ext.lieu == "Clairville"


async def test_low_confidence_keeps_identity() -> None:
    ext, _, status = await analyze_one(
        DummyLow(),
        "Agression à coups de poing",
        "un homme a été agressé à coups de poing",
        0.7,
    )
    assert ext.is_crime
    assert status == "extracted"
    assert ext.auteur.nom == "Lefevre"
    assert ext.confidence == 0.51


async def test_json_retry() -> None:
    dummy = DummyBadThenOk()
    ext, _, status = await analyze_one(
        dummy,
        "Agression à coups de poing",
        "un homme a été agressé à coups de poing",
        0.7,
    )
    assert dummy.n == 2
    assert status == "extracted"
    assert ext.auteur.nom == "Lefevre"
