from sscraping.nlp.filter import might_be_crime, _patterns


def test_prefilter_compiles() -> None:
    assert _patterns()


def test_hit() -> None:
    assert might_be_crime("Agression près d'une gare", "un homme a été agressé")
    assert might_be_crime("Cambriolage", "un vol a eu lieu dans une villa")
    assert might_be_crime("Trafic", "saisie de stupéfiants")


def test_miss_budget() -> None:
    assert not might_be_crime("Budget municipal", "Les élus votent le budget primitif")


def test_viol_not_violence_false_positive() -> None:
    assert not might_be_crime("Concert", "Le violoniste joue un solo")
    assert might_be_crime("Faits divers", "un viol a été signalé")
    assert might_be_crime("Faits divers", "des faits de violence urbaine")
