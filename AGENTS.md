# ss-craping-bot — contrat agent (lire en entier, ne pas élargir)

Pédagogique, démo locale. Rien n’est publié depuis git.
SQLite stocke les identités **en clair** telles qu’extraites de l’article. NULL seulement si le texte ne les donne pas. Pas de masquage SQL. Le masquage est l’affaire d’une GUI (pas dans ce dépôt).

## Objectif
Deux pipelines découplés :
1. scrape → `articles(titre, texte, url, date_publication)`
2. nlp → si sujet ≠ agression : skip ; sinon extraire nom, prenom, nationalite, age, pays_origine, annee, mois, jour (vide si absent)

## Stack (ne pas changer sans raison mesurable)
Python ≥3.12 · asyncio · httpx HTTP/2 · selectolax · aiosqlite WAL · pydantic v2 · PyYAML · typer
NLP : `nlp/connectors/openai_compat.py`. Grok = `api.x.ai` (`grok-4.5`). Local V100 = vLLM ou llama.cpp `/v1`.

## Layout
```
install.sh                 Ubuntu 26.04 only entry
scripts/serve-v100.sh      serveur inférence local
config/sources.yaml        blocs site (listing_url + XPath pagination/article)
config/taxonomy.yaml       labels fermés
src/sscraping/
  cli.py pipeline.py settings.py
  db/schema.sql db/store.py
  http/client.py http/robots.py
  scrape/{base,rss,html,xpath,site,normalize,sources}.py
  nlp/schema.py nlp/filter.py nlp/pipeline.py
  nlp/connectors/{base,openai_compat,grok,v100}.py
tests/  fixtures/
```

## Règles
- Idempotence URL unique. Jamais d’UPDATE destructif du texte (sauf si plus long).
- Défaut DEMO (fixtures). Live HTTP seulement `--live`.
- Préfiltre regex avant LLM. LLM JSON strict validé Pydantic.
- Un article → 0..1 incident. Ne jamais inventer un champ : absent dans le texte → NULL. Ne jamais effacer un champ extrait (pas d’anonymisation SQL, pas de wipe sur confidence).
- Pas de HTML complet en git. Pas de secrets. `.env` local.
- Commentaires : pourquoi, pas quoi. Docstrings module + fonctions publiques.
- Sources live en parallèle, items d’une source en série (`delay_s`). NLP : `nlp_concurrency` puis writes SQLite série.

## Commandes
`./install.sh` · `./install.sh --v100` · `.venv/bin/sscraping scrape` · `sscraping analyze --backend grok|v100` · `sscraping run` · `pytest -q`

## Quand éditer
- Nouveau site → un bloc dans `config/sources.yaml` (listing_url + XPath). Pas de scraper unique magique.
- Prompt NLP → `nlp/pipeline.py` SYSTEM_PROMPT uniquement. Garder Pydantic synchro.
- Nouveau connecteur → sous-classe `OpenAICompatConnector`. Ne pas dupliquer le POST.
- Perf : `CONCURRENCY` / `NLP_CONCURRENCY` dans `.env`.

V100 32 Go : oui. 14B AWQ / 14B GGUF Q4. Pas de 70B.

Détails : `AGENTS.scrape.md` `AGENTS.nlp.md` `AGENTS.install.md`
