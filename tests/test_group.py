from scraping_grok.nlp.group import grouping_key, norm_name
from scraping_grok.nlp.schema import Auteur, Faits, IncidentExtraction


def _ext(nom, prenom, annee=2025, mois=3, jour=3) -> IncidentExtraction:
    return IncidentExtraction(
        is_crime=True,
        type_crime="violences_personnes",
        auteur=Auteur(nom=nom, prenom=prenom),
        faits=Faits(annee=annee, mois=mois, jour=jour),
        confidence=0.9,
    )


def test_norm_accents() -> None:
    assert norm_name("Lefèvre") == "lefevre"
    assert norm_name("Jean-Pierre") == "jean pierre"


def test_same_fait() -> None:
    a = grouping_key(_ext("Lefèvre", "Marc"))
    b = grouping_key(_ext("lefevre", "MARC"))
    assert a is not None and a == b


def test_missing_identity_no_group() -> None:
    assert grouping_key(_ext(None, "Marc")) is None
    assert grouping_key(_ext("Lefevre", None)) is None
    assert grouping_key(_ext("Lefevre", "Marc", jour=None)) is None
