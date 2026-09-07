from sscraping.nlp.filter import might_be_aggression


def test_prefilter_positive() -> None:
    assert might_be_aggression("Agression près d'une gare", "un homme a été agressé")


def test_prefilter_negative() -> None:
    assert not might_be_aggression("Budget municipal", "Les élus votent le budget primitif")
