from scraping_grok.nlp.filter import might_be_crime, _token_sets


def test_prefilter_compiles() -> None:
    strong, weak = _token_sets()
    assert strong and weak


def test_hit_strong() -> None:
    assert might_be_crime("Agression près d'une gare", "un homme a été agressé")
    assert might_be_crime("Cambriolage", "la villa a été visitée")
    assert might_be_crime("Trafic", "saisie de stupéfiants")


def test_miss_budget() -> None:
    assert not might_be_crime("Budget municipal", "Les élus votent le budget primitif")


def test_viol_not_violence_false_positive() -> None:
    assert not might_be_crime("Concert", "Le violoniste joue un solo")
    assert might_be_crime("Faits divers", "un viol a été signalé")
    assert might_be_crime("Faits divers", "des faits de violence urbaine, un homme interpellé")


def test_single_weak_body_not_enough() -> None:
    assert not might_be_crime("Faits divers", "un mot sur la violence au cinéma")
