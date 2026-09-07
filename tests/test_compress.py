from scraping_grok.nlp.compress import compress_for_llm
from scraping_grok.nlp.preuves import local_preuves


def test_compress_keeps_lead_and_identity() -> None:
    texte = (
        "Un homme a été agressé à coups de poing près de la gare.\n\n"
        "Selon le parquet, l'auteur prénommé Marc, nommé Lefevre, âgé de 34 ans, a été interpellé.\n\n"
        "Lire aussi : la météo. Newsletter. Un long aparté sans rapport " + ("bla " * 400)
    )
    out = compress_for_llm("Agression à la gare", texte, max_chars=1800)
    assert "TITRE:" in out
    assert "Marc" in out
    assert "Lefevre" in out
    assert "34" in out
    assert len(out) < 2000
    assert "bla bla" not in out or out.count("bla") < 50


def test_local_preuves() -> None:
    qs = local_preuves("Agression", "Un homme a été agressé à coups de poing. Le budget est voté.")
    assert qs
    assert any("agressé" in q.lower() for q in qs)
