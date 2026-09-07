# Scraping Grok Support — contrat agent (lire en entier, ne pas élargir)

Pédagogique, démo locale. Rien n’est publié depuis git.
PostgreSQL stocke les identités **en clair**. NULL si absent du texte. Pas de masquage SQL.

## Objectif
1. scrape (Scrapy) → `articles`
2. nlp (Grok) → si ≠ crime : skip ; sinon `type_crime` (8 groupes) + auteur + date des faits
3. triage → `faits` : même nom+prénom+date (normalisés) = un seul fait, N articles

## Stack
Python ≥3.12 · Scrapy · PostgreSQL/psycopg3 · Grok `api.x.ai` (`grok-4.5`) · pydantic v2 · typer

Logs DEBUG : `logs/{scraping_grok,scrapy,sql,nlp}.log`. `--quiet` = INFO.

## Layout
```
install.sh  docker-compose.yml  scripts/init-db.sh
config/sources.yaml  config/taxonomy.yaml
src/scraping_grok/
  cli.py pipeline.py settings.py logconfig.py
  db/{schema.sql,sql.py,store.py}
  crawler/{..., known.py, spiders/site.py, spiders/rss.py}
  nlp/{pipeline,compress,filter,preuves,group,schema}.py
  nlp/connectors/{openai_compat,grok}.py
```

## Règles
- URL unique. Skip GET si URL déjà en PG.
- LLM : préfiltre → compressé → 1 retry JSON → preuves locales. Articles `ignored`/`extracted`/`error` jamais renvoyés au LLM.
- Probe : `scraping-grok probe --source ID` (XPath, mur cookies). Playwright seulement si probe le dit.
- Un article → 0..1 incident. Groupage seulement si nom, prénom, année, mois, jour tous présents.
- Ne jamais inventer un champ. Ne jamais anonymiser en SQL.

## Commandes
`./install.sh` · `scraping-grok db-init` · `scraping-grok scrape --live` · `scraping-grok analyze` · `scraping-grok probe --source ID` · `scraping-grok triage` · `pytest -q`

Prompt NLP → `nlp/pipeline.py` SYSTEM_PROMPT uniquement (rester identique d’un appel à l’autre).
