from sscraping.nlp.filter import might_be_aggression, _patterns


def test_prefilter_positive() -> None:
    _patterns.cache_clear()
    assert might_be_aggression("Agression près d'une gare", "un homme a été agressé")


def test_prefilter_negative() -> None:
    _patterns.cache_clear()
    assert not might_be_aggression("Budget municipal", "Les élus votent le budget primitif")


def test_viol_does_not_match_inside_unrelated() -> None:
    _patterns.cache_clear()
    assert not might_be_aggression("Concert", "Le violoniste joue un solo")
    assert might_be_aggression("Faits divers", "un viol a été signalé")
    assert might_be_aggression("Faits divers", "des faits de violence urbaine")
