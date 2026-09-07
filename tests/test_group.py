from datetime import date, timedelta

from scraping_grok.nlp.group import date_window, grouping_key, named_auteurs, titles_similar, norm_name
from scraping_grok.nlp.schema import Auteur, Faits, IncidentExtraction


def _ext(nom, prenom, annee=2025, mois=3, jour=3, lieu=None, extra=None) -> IncidentExtraction:
    auteurs = [Auteur(nom=nom, prenom=prenom)]
    if extra:
        auteurs.append(Auteur(nom=extra[0], prenom=extra[1]))
    return IncidentExtraction(
        is_crime=True,
        type_crime="violences_personnes",
        auteur=Auteur(nom=nom, prenom=prenom),
        auteurs=auteurs,
        lieu=lieu,
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


def test_named_auteurs_multi() -> None:
    ext = _ext("Lefevre", "Marc", extra=("Durand", "Paul"))
    assert ("lefevre", "marc") in named_auteurs(ext)
    assert ("durand", "paul") in named_auteurs(ext)


def test_date_window() -> None:
    lo, hi = date_window(date(2025, 3, 3))
    assert lo == date(2025, 3, 2)
    assert hi == date(2025, 3, 4)
    assert hi - lo == timedelta(days=2)


def test_title_similar() -> None:
    assert titles_similar("agression a la gare de clairville", "agression pres de la gare de clairville")
    assert not titles_similar("budget municipal 2026", "agression a la gare")
