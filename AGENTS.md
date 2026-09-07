# ss-craping-bot — contrat agent (lire en entier, ne pas élargir)

Pédagogique, démo locale. Rien n’est publié depuis git.
PostgreSQL stocke les identités **en clair** telles qu’extraites de l’article. NULL seulement si le texte ne les donne pas. Pas de masquage SQL. Le masquage est l’affaire d’une GUI (pas dans ce dépôt).

## Objectif
Deux pipelines découplés :
1. scrape (Scrapy) → `articles(titre, texte, url, date_publication)`
2. nlp → si sujet ≠ agression : skip ; sinon extraire nom, prenom, nationalite, age, pays_origine, annee, mois, jour (vide si absent)

## Stack (ne pas changer sans raison mesurable)
Python ≥3.12 · Scrapy + parsel XPath · PostgreSQL + psycopg3 · asyncio NLP · httpx (LLM) · pydantic v2 · PyYAML · typer
NLP : `nlp/connectors/openai_compat.py`. Grok = `api.x.ai` (`grok-4.5`). Local V100 = vLLM ou llama.cpp `/v1`.

Logs DEBUG par défaut : `logs/sscraping.log`, `logs/scrapy.log`, `logs/sql.log`, `logs/nlp.log`. `--quiet` = INFO.

## Layout
```
install.sh                 Ubuntu 26.04 only entry
docker-compose.yml         PostgreSQL 16
scripts/init-db.sh         docker compose ou rôle local
scripts/serve-v100.sh
config/sources.yaml        blocs site (listing_url + XPath)
src/sscraping/
  cli.py pipeline.py settings.py logconfig.py
  db/{schema.sql,sql.py,store.py}
  crawler/{settings,items,extract,pipelines,middlewares,extensions,runner}.py
  crawler/spiders/{site,rss}.py
  scrape/{base,rss,html,normalize,sources}.py
  nlp/...
tests/  fixtures/  logs/
```

## Règles
- Idempotence URL unique. Jamais d’UPDATE destructif du texte (sauf si plus long).
- Défaut DEMO (fixtures). Live HTTP seulement `--live` (Scrapy).
- Préfiltre regex avant LLM. LLM JSON strict validé Pydantic.
- Un article → 0..1 incident. Ne jamais inventer un champ : absent dans le texte → NULL. Ne jamais effacer un champ extrait.
- Pas de HTML complet en git. Pas de secrets. `.env` local.
- Commentaires : pourquoi, pas quoi.
- Live : Scrapy (robots, delay, 1 req/domaine). NLP : `nlp_concurrency` puis writes PG série.
- Verbosity : logger DEBUG, XPath match counts, chaque REQ/RES, chaque UPSERT.

## Commandes
`./install.sh` · `sscraping db-init` · `sscraping scrape --live` · `sscraping analyze --backend grok|v100` · `pytest -q`

## Quand éditer
- Nouveau site → un bloc `config/sources.yaml`. Spider générique, pas de classe par site.
- Prompt NLP → `nlp/pipeline.py` SYSTEM_PROMPT. Pydantic synchro.
- Nouveau connecteur → sous-classe `OpenAICompatConnector`.
- Perf : `CONCURRENCY` / `NLP_CONCURRENCY` / `DOWNLOAD_DELAY` via `delay_s` YAML.

V100 32 Go : oui. 14B AWQ / 14B GGUF Q4. Pas de 70B.

Détails : `AGENTS.scrape.md` `AGENTS.nlp.md` `AGENTS.install.md`
